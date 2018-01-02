import datetime
import json
import math
import operator

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import (
        render, redirect, get_object_or_404,
        )
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

from constants import *
from forms import *
from models import *

PAGE_SIZE = 50

class JsonResponse(HttpResponse):
    '''
    this class makes it easier to quickly turn content into json and
    return it as a response
    '''

    def __init__(self, content, content_type="application/json", *args, **kwargs):
        if content:
            content = json.dumps(content)
        else:
            content = json.dumps({})
        super(JsonResponse, self).__init__(content, content_type=content_type, *args, **kwargs)


def index(request):
    return redirect(reverse(search_recipes))


@login_required(login_url="/accounts/login/")
def bookmarklet(request):
    ctx = {
        'add': True,
        'hide_page_header': True,
    }

    saved = _save_recipe(request, ctx)

    if saved:
        return redirect(reverse(search_recipes), permanent=True)

    return render(request, 'bookmarklet.html', ctx)


@login_required(login_url="/accounts/login/")
def add_recipe(request):
    ctx = {
        'add': True,
    }

    recipe = None
    if request.method == 'GET':
        recipe_id = request.GET.get('recipe', None)
        if recipe_id is not None:
            try:
                recipe = Recipe.objects.get(id=recipe_id)
            except ObjectDoesNotExist:
                pass

    saved = _save_recipe(request, ctx, recipe=recipe)

    if saved:
        return redirect(reverse(search_recipes), permanent=True)
    else:
        return render(request, 'edit_recipe.html', ctx)


def _save_recipe(request, ctx, ribbon=None, recipe=None):
    """
    core function for adding/editing/saving recipes
    """

    # try to associate with an existing recipe if it exists
    if request.method == 'GET' and not recipe:
        url = request.GET.get('url', None)
        title = request.GET.get('title', None)
        if url:
            try:
                recipe = Recipe.objects.get(link=url)
            except ObjectDoesNotExist:
                pass

    # staff can add a ribbon as someone else
    if request.user.is_staff:
        ctx['users'] = User.objects.all()
        ctx['user_id'] = request.user.id
        specified_user = request.user
        if request.POST:
            ctx['user_id'] = int(request.POST.get('user', request.user.id))
            try:
                specified_user = User.objects.get(id=ctx['user_id'])
            except ObjectDoesNotExist:
                pass

    ctx['all_tags'] = json.dumps(list(Tag.objects.values_list(
        'value', flat=True).order_by('value').distinct()))
    if ribbon and not recipe:
        recipe = ribbon.recipe

    # try to guess the recipe if it's a POST and there isn't one given
    if not recipe and request.method == 'POST':
        recipe_id = request.POST.get('recipe-id', None)
        if recipe_id:
            try:
                recipe = Recipe.objects.get(id=recipe_id)
            except ObjectDoesNotExist:
                pass
        else:
            link = request.POST.get('re-link', None)
            if link:
                try:
                    recipe = Recipe.objects.get(link=link)
                except ObjectDoesNotExist:
                    pass

    # try to find the ribbon if possible
    if recipe and not ribbon:
        try:
            ribbon = Ribbon.objects.get(recipe=recipe, user=request.user)
        except ObjectDoesNotExist:
            pass

    recipe_form = RecipeForm(
            request.POST or None, prefix="re", instance=recipe)
    ribbon_form = RibbonForm(
            request.POST or None, prefix="ri", instance=ribbon)

    saved = False
    if recipe_form.is_valid() and ribbon_form.is_valid():
        recipe = recipe_form.save(commit=False)
        recipe.save()
        ribbon = ribbon_form.save(commit=False)
        ribbon.recipe = recipe
        if request.user.is_staff:
            ribbon.user = specified_user
        else:
            ribbon.user = request.user
        ribbon.save()

        my_current_tags = {tag.value: tag for tag in ribbon.tag_set.all()}
        tags = request.POST.get('tags','').split(',')
        for value in tags:
            if not value:
                continue
            if not value in my_current_tags:
                # add it
                Tag.objects.create(ribbon=ribbon, value=value)
            else:
                # don't delete it later
                del my_current_tags[value]
        for removed_tag in my_current_tags.values():
            removed_tag.delete()
        saved = True
    elif recipe_form.errors or ribbon_form.errors:
        tags = request.POST.get('tags','').split(',')
    else:
        if ribbon:
            tags = list(ribbon.tag_set.values_list('value', flat=True))
        elif recipe and request.user.userprofile.copy_tags:
            tags = list(Tag.objects.filter(ribbon__recipe=recipe).values_list(
                'value', flat=True).distinct())
        else:
            tags = ''

    ctx.update({
        'recipe_form': recipe_form,
        'ribbon_form': ribbon_form,
        'ribbon': ribbon,
        'recipe': recipe,
        'tags': ','.join(tags),
        })

    if request.method == 'GET':
        url = request.GET.get('url', None)
        title = request.GET.get('title', None)
        if not recipe:
            if url:
                ctx['recipe_form'].initial['link'] = url
            if title:
                ctx['recipe_form'].initial['title'] = title

    return saved


@login_required(login_url="/accounts/login/")
def edit_recipe(request, ribbon_id):
    ctx = {
        'edit': True,
    }
    try:
        ribbon = Ribbon.objects.get(id=ribbon_id, user=request.user)
    except ObjectDoesNotExist:
        return redirect(reverse(search_recipes), permanent=True)

    saved = _save_recipe(request, ctx, ribbon)
    if saved:
        ctx['message'] = 'Recipe successfully saved.'
    return render(request, 'edit_recipe.html', ctx)


def _paginate_content(request, ctx, key="ribbons"):
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        if page == 'all':
            ctx[page] = 'all'
            return
        if not page:
            page = 1
        page = int(page)
        page_size = int(request.GET.get('page_size', PAGE_SIZE))
    else:
        page = 1
        page_size = PAGE_SIZE

    ctx['num_pages'] = int(math.ceil(ctx[key].count() / float(page_size)))

    ctx[key] = ctx[key][(page - 1) * page_size: page * page_size]
    if key == 'ribbons':
        ctx['ribbons'] = ctx['ribbons'].select_related('recipe')

    ctx['page_range'] = xrange(1, ctx['num_pages'] + 1)
    ctx['page'] = page


def view_recipe(request, recipe_id):
    ctx = {}

    recipe = get_object_or_404(Recipe, id=recipe_id)

    if request.user.is_authenticated():
        try:
            ribbon = Ribbon.objects.get(recipe=recipe, user=request.user)
            ctx['ribbon'] = ribbon
            ctx['other_ribbons'] = Ribbon.objects.filter(recipe=recipe).exclude(id=ribbon.id)
            my_tags = ribbon.get_tags()
            all_tags = recipe.get_tags()

            other_tags = sorted(set(all_tags) - set(my_tags))

            ctx['my_tags'] = my_tags
            ctx['other_tags'] = other_tags

        except ObjectDoesNotExist:
            ctx['other_ribbons'] = Ribbon.objects.filter(recipe=recipe)
            ctx['other_tags'] = recipe.get_tags()


    ctx['recipe'] = recipe

    return render(request, 'view_recipe.html', ctx)


@require_http_methods(["GET"])
def search_recipes(request):
    ctx = {}

    all_ribbons = request.GET.get('all', False) or \
        not request.user.is_authenticated()
    ctx['own_ribbons'] = not all_ribbons
    if all_ribbons:
        ribbons = Ribbon.objects.all()
    else:
        ribbons = Ribbon.objects.filter(user=request.user)

    if request.user.is_authenticated():
        if request.GET.get('recipebox'):
            ctx['recipe_box'] = True
            ribbons = ribbons.filter(user=request.user, is_boxed=True).order_by(
                '-boxed_on', '-time_created')
        if request.GET.get('thumbsup'):
            ctx['thumbs_up'] = True
            ribbons = ribbons.filter(user=request.user, thumb=True)
        if request.GET.get('used'):
            ctx['used'] = True
            ribbons = ribbons.filter(user=request.user, is_used=True)

    query = request.GET.get('q')
    if query:
        ctx['query'] = query
        ribbons = ribbons.filter(reduce(operator.and_,
            (Q(recipe__title__icontains=token) | Q(tag__value__icontains=token)
            for token in query.split(',') if token)))

    ribbons = ribbons.distinct()
    ctx['ribbons'] = ribbons
    _paginate_content(request, ctx, 'ribbons')

    tags = Tag.objects.filter(ribbon__in=ribbons).values('value').annotate(
        count=Count('value')).order_by('value')

    if all_ribbons:
        ctx['recipes'] = Recipe.objects.filter(
            ribbon__in=ribbons).distinct()
        _paginate_content(request, ctx, 'recipes')

    ctx['search_tags_json'] = json.dumps(list(tags))

    return render(request, 'search.html', ctx)


@login_required(login_url="/accounts/login/")
def delete_ribbon(request, ribbon_id):
    try:
        ribbon = Ribbon.objects.get(id=ribbon_id, user=request.user)
    except ObjectDoesNotExist:
        return JsonResponse('ERROR')
    recipe = ribbon.recipe
    ribbon.delete()
    if not recipe.ribbon_set.exists():
        recipe.delete();
    return JsonResponse('OK')


@login_required(login_url="/accounts/login/")
def action(request):
    if not request.method == 'POST':
        return JsonResponse({'status':'OK'})
    action = request.POST.get('action', None)
    if action == 'deleteRibbon':
        recipe_id = request.POST.get('recipeId', None)
        ribbon_id = request.POST.get('ribbonId', None)
        try:
            ribbon = Ribbon.objects.get(id=ribbon_id, user=request.user)
        except ObjectDoesNotExist:
            return JsonResponse('ERROR')
        recipe = ribbon.recipe
        ribbon.delete()
        if not recipe.ribbon_set.exists():
            recipe.delete()
        return JsonResponse('OK')
    elif action == 'changeBoxStatus':
        new_status = request.POST.get('newStatus', None) == 'true'
        recipe_id = request.POST.get('recipeId', None)
        ribbon_id = request.POST.get('ribbonId', None)
        if recipe_id:
            try:
                recipe = Recipe.objects.get(id=recipe_id)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'FAIL'})
        else:
            return JsonResponse({'status': 'FAIL'})
        copy_tags = False
        try:
            ribbon = Ribbon.objects.get(id=ribbon_id)
            if ribbon.recipe != recipe:
                return JsonResponse({'status': 'FAIL'})
        except ObjectDoesNotExist:
            ribbon = Ribbon(recipe=recipe, user=request.user)
            copy_tags = request.user.userprofile.copy_tags
        ribbon.is_boxed = new_status
        if ribbon.is_boxed:
            ribbon.boxed_on = datetime.datetime.now()
        ribbon.save()
        if copy_tags:
            tags = Tag.objects.filter(ribbon__recipe=recipe)
            for tag in tags:
                Tag(key=tag.key, value=tag.value, ribbon=ribbon).save()

        return JsonResponse({'status': 'OK', 'ribbonId': ribbon.id})

    else:
        return JsonResponse({'status':'OK'})
