from django.urls import path,  include
from . import views
app_name = 'promptapp'

urlpatterns = [
    path('', views.promptActionPage, name='promptActionPage'), 
    path('queryPromptText', views.query_prompt_text, name='query_prompt_text'),
    path('updateMemory', views.update_memory, name='updateMemory'),
    path('instructionsset', views.instructions_set, name='instructions_set'),  
    path('save-or-edit-instruction/', views.save_or_edit_instruction, name='save_or_edit_instruction'),
    path('delete-instruction/', views.delete_instruction, name='delete_instruction'),
    path('clear_memory/', views.clear_memory, name='clear_memory'),
    path('setting_page/', views.setting_page, name='setting_page'),
    path('save_claude_api/', views.save_claude_api, name='save_claude_api'),
    path('save_openai_api/', views.save_openai_api, name='save_openai_api'),

]