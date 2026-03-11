import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Recipe, Ribbon, Tag


def make_user(username="testuser", password="pass"):
    user = User.objects.create_user(username=username, password=password)
    return user


def make_recipe(title="Test Recipe", link=None):
    return Recipe.objects.create(title=title, link=link)


def make_ribbon(user, recipe, is_boxed=False, is_used=False, thumb=None):
    return Ribbon.objects.create(
        user=user, recipe=recipe, is_boxed=is_boxed, is_used=is_used, thumb=thumb
    )


class RecipeModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.recipe = make_recipe("Pasta", "https://example.com/pasta")
        self.ribbon = make_ribbon(self.user, self.recipe, thumb=True)
        Tag.objects.create(ribbon=self.ribbon, value="italian")

    def test_str(self):
        self.assertEqual(str(self.recipe), "Pasta")

    def test_get_domain(self):
        self.assertEqual(self.recipe.get_domain(), "example.com")

    def test_get_domain_no_link(self):
        r = make_recipe("No Link")
        self.assertIsNone(r.get_domain())

    def test_get_tags(self):
        self.assertEqual(self.recipe.get_tags(), ["italian"])

    def test_get_thumbs_up_count(self):
        self.assertEqual(self.recipe.get_thumbs_up_count(), 1)

    def test_get_thumbs_down_count(self):
        make_ribbon(make_user("u2"), self.recipe, thumb=False)
        self.assertEqual(self.recipe.get_thumbs_down_count(), 1)

    def test_get_used_count(self):
        make_ribbon(make_user("u3"), self.recipe, is_used=True)
        self.assertEqual(self.recipe.get_used_count(), 1)

    def test_save_empty_link_becomes_null(self):
        r = Recipe(title="No Link", link="")
        r.save()
        self.assertIsNone(r.link)


class RibbonModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.recipe = make_recipe("Soup")
        self.ribbon = make_ribbon(self.user, self.recipe)
        Tag.objects.create(ribbon=self.ribbon, value="soup")

    def test_str(self):
        self.assertIn("Soup", str(self.ribbon))
        self.assertIn("testuser", str(self.ribbon))

    def test_get_tags(self):
        self.assertEqual(self.ribbon.get_tags(), ["soup"])


class SearchRecipesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.recipe = make_recipe("Chocolate Cake", "https://example.com/cake")
        self.ribbon = make_ribbon(self.user, self.recipe)
        Tag.objects.create(ribbon=self.ribbon, value="dessert")
        self.url = reverse("search_recipes")

    def test_anonymous_sees_all_recipes(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_logged_in_sees_own_ribbons(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ribbon, response.context["ribbons"])

    def test_search_by_title(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"q": "Chocolate"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ribbon, response.context["ribbons"])

    def test_search_by_tag(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"q": "dessert"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ribbon, response.context["ribbons"])

    def test_search_no_match(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"q": "zzznothing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["ribbons"]), 0)

    def test_filter_recipe_box(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"recipebox": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["ribbons"]), 0)

    def test_filter_thumbsup(self):
        self.client.login(username="testuser", password="pass")
        boxed_ribbon = make_ribbon(self.user, make_recipe("Soup"), thumb=True)
        response = self.client.get(self.url, {"thumbsup": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(boxed_ribbon, response.context["ribbons"])
        self.assertNotIn(self.ribbon, response.context["ribbons"])

    def test_filter_used(self):
        self.client.login(username="testuser", password="pass")
        used_ribbon = make_ribbon(self.user, make_recipe("Steak"), is_used=True)
        response = self.client.get(self.url, {"used": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(used_ribbon, response.context["ribbons"])
        self.assertNotIn(self.ribbon, response.context["ribbons"])

    def test_filter_unused(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"unused": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ribbon, response.context["ribbons"])


class AddRecipeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse("add_recipe")

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next=" + self.url)

    def test_get_shows_form(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("recipe_form", response.context)

    def test_post_creates_recipe_and_ribbon(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url,
            {
                "re-title": "New Recipe",
                "re-link": "https://example.com/new",
                "re-servings": "",
                "re-description": "",
                "re-ingredients": "",
                "re-directions": "",
                "ri-comments": "",
                "ri-is_boxed": False,
                "ri-is_used": False,
                "tags": "italian,pasta",
            },
        )
        self.assertEqual(response.status_code, 301)
        self.assertTrue(Recipe.objects.filter(title="New Recipe").exists())
        recipe = Recipe.objects.get(title="New Recipe")
        self.assertTrue(Ribbon.objects.filter(recipe=recipe, user=self.user).exists())

    def test_post_creates_tags(self):
        self.client.login(username="testuser", password="pass")
        self.client.post(
            self.url,
            {
                "re-title": "Tagged Recipe",
                "re-link": "",
                "re-servings": "",
                "re-description": "",
                "re-ingredients": "",
                "re-directions": "",
                "ri-comments": "",
                "ri-is_boxed": False,
                "ri-is_used": False,
                "tags": "spicy,asian",
            },
        )
        recipe = Recipe.objects.get(title="Tagged Recipe")
        ribbon = Ribbon.objects.get(recipe=recipe, user=self.user)
        tag_values = set(ribbon.tag_set.values_list("value", flat=True))
        self.assertEqual(tag_values, {"spicy", "asian"})

    def test_post_reuses_existing_recipe(self):
        existing = make_recipe("Existing", "https://example.com/existing")
        self.client.login(username="testuser", password="pass")
        self.client.post(
            self.url,
            {
                "re-title": "Existing",
                "re-link": "https://example.com/existing",
                "re-servings": "",
                "re-description": "",
                "re-ingredients": "",
                "re-directions": "",
                "ri-comments": "",
                "ri-is_boxed": False,
                "ri-is_used": False,
                "tags": "",
                "recipe-id": existing.id,
            },
        )
        self.assertEqual(Recipe.objects.filter(link="https://example.com/existing").count(), 1)


class EditRecipeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.recipe = make_recipe("Old Title", "https://example.com/old")
        self.ribbon = make_ribbon(self.user, self.recipe)

    def test_redirect_if_not_logged_in(self):
        url = reverse("edit_recipe", args=[self.ribbon.id])
        response = self.client.get(url)
        self.assertRedirects(response, "/accounts/login/?next=" + url)

    def test_get_shows_form(self):
        self.client.login(username="testuser", password="pass")
        url = reverse("edit_recipe", args=[self.ribbon.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("recipe_form", response.context)

    def test_post_updates_recipe(self):
        self.client.login(username="testuser", password="pass")
        url = reverse("edit_recipe", args=[self.ribbon.id])
        self.client.post(
            url,
            {
                "re-title": "New Title",
                "re-link": "https://example.com/old",
                "re-servings": "",
                "re-description": "",
                "re-ingredients": "",
                "re-directions": "",
                "ri-comments": "Updated",
                "ri-is_boxed": False,
                "ri-is_used": False,
                "tags": "",
            },
        )
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "New Title")

    def test_edit_other_users_ribbon_redirects(self):
        other_user = make_user("other")
        other_recipe = make_recipe("Other", "https://example.com/other")
        other_ribbon = make_ribbon(other_user, other_recipe)
        self.client.login(username="testuser", password="pass")
        url = reverse("edit_recipe", args=[other_ribbon.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)


class DeleteRibbonViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.recipe = make_recipe("To Delete")
        self.ribbon = make_ribbon(self.user, self.recipe)

    def test_delete_ribbon(self):
        self.client.login(username="testuser", password="pass")
        url = reverse("delete_ribbon", args=[self.ribbon.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ribbon.objects.filter(id=self.ribbon.id).exists())

    def test_delete_ribbon_also_deletes_orphan_recipe(self):
        self.client.login(username="testuser", password="pass")
        url = reverse("delete_ribbon", args=[self.ribbon.id])
        self.client.get(url)
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_delete_ribbon_keeps_recipe_if_other_ribbons_exist(self):
        other_user = make_user("other")
        make_ribbon(other_user, self.recipe)
        self.client.login(username="testuser", password="pass")
        url = reverse("delete_ribbon", args=[self.ribbon.id])
        self.client.get(url)
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_delete_other_users_ribbon_returns_error(self):
        other_user = make_user("other")
        other_recipe = make_recipe("Other Recipe")
        other_ribbon = make_ribbon(other_user, other_recipe)
        self.client.login(username="testuser", password="pass")
        url = reverse("delete_ribbon", args=[other_ribbon.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, "ERROR")


class ActionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.recipe = make_recipe("Action Recipe")
        self.ribbon = make_ribbon(self.user, self.recipe)
        self.url = reverse("action")

    def test_get_returns_ok(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_ribbon_action(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url,
            {
                "action": "deleteRibbon",
                "recipeId": self.recipe.id,
                "ribbonId": self.ribbon.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ribbon.objects.filter(id=self.ribbon.id).exists())

    def test_change_box_status_true(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url,
            {
                "action": "changeBoxStatus",
                "recipeId": self.recipe.id,
                "ribbonId": self.ribbon.id,
                "newStatus": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.ribbon.refresh_from_db()
        self.assertTrue(self.ribbon.is_boxed)

    def test_change_box_status_false(self):
        self.ribbon.is_boxed = True
        self.ribbon.save()
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url,
            {
                "action": "changeBoxStatus",
                "recipeId": self.recipe.id,
                "ribbonId": self.ribbon.id,
                "newStatus": "false",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.ribbon.refresh_from_db()
        self.assertFalse(self.ribbon.is_boxed)

    def test_change_box_status_creates_ribbon_if_missing(self):
        new_recipe = make_recipe("New Recipe")
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url,
            {
                "action": "changeBoxStatus",
                "recipeId": new_recipe.id,
                "ribbonId": 99999,
                "newStatus": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "OK")
        self.assertTrue(Ribbon.objects.filter(recipe=new_recipe, user=self.user).exists())
