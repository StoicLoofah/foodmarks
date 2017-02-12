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

    def __init__(self, content, mimetype="application/json", *args, **kwargs):
        if content:
            content = json.dumps(content)
        else:
            content = json.dumps({})
        super(JsonResponse, self).__init__(content, mimetype, *args, **kwargs)


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

    ctx['known_values_to_keys'] = known_values_to_keys
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

        tags = json.loads(request.POST['tag-json'])
        for key in tags:
            for value in tags[key]:
                if value == '':
                    value = None
                if tags[key][value].get('id'):  # update if possible
                    tag = Tag.objects.get(id=tags[key][value]['id'])
                    if tags[key][value].get('deleted', False):
                        tag.delete()
                elif not tags[key][value].get('deleted', False):  # create
                    Tag(ribbon=ribbon, key=key, value=value).save()
        saved = True
    elif recipe_form.errors or ribbon_form.errors:
        tags = json.loads(request.POST['tag-json'])
    else:
        tags = {}
        if ribbon:
            actual_tags = ribbon.tag_set.all()
            for actual_tag in actual_tags:
                if not actual_tag.key in tags:
                    tags[actual_tag.key] = {}
                tags[actual_tag.key][actual_tag.value] = \
                    {'id': actual_tag.id}
        elif recipe and request.user.get_profile().copy_tags:
            actual_tags = Tag.objects.filter(ribbon__recipe=recipe)
            for actual_tag in actual_tags:
                if not actual_tag.key in tags:
                    tags[actual_tag.key] = {}
                tags[actual_tag.key][actual_tag.value] = {}

    ctx.update({
        'recipe_form': recipe_form,
        'ribbon_form': ribbon_form,
        'ribbon': ribbon,
        'recipe': recipe,
        'tags': tags,
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
            my_tags = ribbon.get_tag_dict()
            all_tags = recipe.get_tag_dict()

            other_tags = {}

            for key, values in all_tags.items():
                if key in my_tags:
                    temp = [value for value in values if value not in my_tags[key]]
                    if temp:
                        other_tags[key] = temp
                else:
                    other_tags[key] = values

            ctx['my_tags'] = my_tags
            ctx['other_tags'] = other_tags

        except ObjectDoesNotExist:
            ctx['other_ribbons'] = Ribbon.objects.filter(recipe=recipe)
            ctx['other_tags'] = recipe.get_tag_dict()


    ctx['recipe'] = recipe

    return render(request, 'view_recipe.html', ctx)


def _get_key_order(val):
    key = val[0]
    try:
        index = ordered_known_keys.index(key)
        return '{0: 3d}'.format(index)
    except ValueError:
        return '{0: 3d}{1}'.format(len(ordered_known_keys), key)


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

    if request.user.is_authenticated() and request.GET.get('recipebox'):
        ctx['recipe_box'] = True
        ribbons = ribbons.filter(user=request.user, is_boxed=True).order_by(
            '-boxed_on', '-time_created')

    query_string = request.GET.get('q', '')
    if query_string != '':
        ctx['q'] = query_string
        ribbons = ribbons.filter(reduce(operator.and_,
            (Q(recipe__title__icontains=token)
            for token in query_string.split(' ') if token)))

    selected_tags = request.GET.getlist('tag')
    if selected_tags:
        split_selected_tags = map(lambda s:s.split(':'), selected_tags)

        for split_selected_tag in split_selected_tags:
            ribbons = ribbons.filter(tag__key=split_selected_tag[0], tag__value=split_selected_tag[1])

    ctx['ribbons'] = ribbons
    _paginate_content(request, ctx, 'ribbons')

    tags = Tag.objects.filter(ribbon__in=ribbons).values('key', 'value').annotate(count=Count('value')).order_by('value')
    for tag in tags:
        if tag['key'] + ':' + tag['value'] in selected_tags:
            tag['selected'] = True

    if all_ribbons:
        ctx['recipes'] = Recipe.objects.filter(
            ribbon__in=ribbons).distinct()
        _paginate_content(request, ctx, 'recipes')

    ctx['search_tags'] = tags

    return render(request, 'search.html', ctx)


@login_required(login_url="/accounts/login/")
def delete_ribbon(request, ribbon_id):
    try:
        ribbon = Ribbon.objects.get(id=ribbon_id, user=request.user)
    except ObjectDoesNotExist:
        return HttpResponse('ERROR', mimetype="application/json")
    recipe = ribbon.recipe
    ribbon.delete()
    if not recipe.ribbon_set.exists():
        recipe.delete();
    return HttpResponse('OK', mimetype="application/json")


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
            return HttpResponse('ERROR', mimetype="application/json")
        recipe = ribbon.recipe
        ribbon.delete()
        if not recipe.ribbon_set.exists():
            recipe.delete()
        return HttpResponse('OK', mimetype="application/json")
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
            copy_tags = request.user.get_profile().copy_tags
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


@login_required(login_url="/accounts/login/")
def get_tag_category(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'OK'})
    value = request.GET.get('value', None)
    if not value:
        return JsonResponse({'status': 'OK', 'categories': ['']})
    seen_categories = set()
    categories = []

    users_tags = Tag.objects.filter(value=value, ribbon__user=request.user).values('key').annotate(count=Count('key')).order_by('-count')
    for tag in users_tags:
        categories.append(tag['key'])
        seen_categories.add(tag['key'])

    known_key = known_values_to_keys.get(value, None)
    if known_key and not known_key in seen_categories:
        categories.append(known_key)
        seen_categories.add(known_key)

    other_tags = Tag.objects.filter(value=value).values('key').annotate(count=Count('key')).order_by('-count')
    for tag in other_tags:
        if not tag['key'] in seen_categories:
            categories.append(tag['key'])
            seen_categories.add(tag['key'])

    return JsonResponse({'status': 'OK', 'categories': categories})
