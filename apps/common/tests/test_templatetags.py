from django.test import TestCase, Client
from django.template import Template, Context


class AddClassFilterTests(TestCase):
    def test_add_class_on_field(self):
        from django import forms

        class SimpleForm(forms.Form):
            name = forms.CharField()

        form = SimpleForm()
        field = form['name']
        tpl = Template("{% load class_filters %}{{ field|add_class:'form-control' }}")
        rendered = tpl.render(Context({'field': field}))
        # should include the class attribute
        self.assertIn('class="form-control"', rendered)


class AuthPagesSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_page(self):
        r = self.client.get('/accounts/login/')
        self.assertEqual(r.status_code, 200)

    def test_signup_page(self):
        r = self.client.get('/accounts/signup/')
        self.assertEqual(r.status_code, 200)

    def test_password_reset_page(self):
        r = self.client.get('/accounts/password/reset/')
        self.assertEqual(r.status_code, 200)

    def test_password_reset_done_page(self):
        r = self.client.get('/accounts/password/reset/done/')
        self.assertEqual(r.status_code, 200)
