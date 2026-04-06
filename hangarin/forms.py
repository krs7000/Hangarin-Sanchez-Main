from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Category, Note, Priority, SubTask, Task


class HangarinAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "auth-input",
                "placeholder": "Username",
                "autocomplete": "username",
            }
        )
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-input",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = ""
        self.fields["password"].label = ""


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if type(field.widget) in (forms.TextInput, forms.EmailInput):
                field.widget.attrs.update({"class": "search-input", "style": "width: 100%; margin-top: 0.5rem; margin-bottom: 1rem;"})
            elif type(field.widget) == forms.Select:
                field.widget.attrs.update({"class": "search-input", "style": "width: 100%; margin-top: 0.5rem; margin-bottom: 1rem; padding: 0.5rem;"})
            elif type(field.widget) == forms.Textarea:
                field.widget.attrs.update({"class": "search-input", "style": "width: 100%; margin-top: 0.5rem; margin-bottom: 1rem; min-height: 120px;"})
            elif type(field.widget) == forms.DateTimeInput:
                field.widget.attrs.update({"class": "search-input", "type": "datetime-local", "style": "width: 100%; margin-top: 0.5rem; margin-bottom: 1rem;"})
            elif type(field.widget) == forms.DateInput:
                field.widget.attrs.update({"class": "search-input", "type": "date", "style": "width: 100%; margin-top: 0.5rem; margin-bottom: 1rem;"})


class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "category", "priority", "deadline"]


class SubTaskForm(StyledModelForm):
    class Meta:
        model = SubTask
        fields = ["parent_task", "title", "status"]


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class PriorityForm(StyledModelForm):
    class Meta:
        model = Priority
        fields = ["name"]


class NoteForm(StyledModelForm):
    class Meta:
        model = Note
        fields = ["task", "content"]
