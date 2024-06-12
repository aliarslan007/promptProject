from django.urls import path,  include
from . import views
app_name = 'promptapp'

urlpatterns = [
    path('', views.promptActionPage, name='promptActionPage'), 
    path('queryPromptText', views.query_prompt_text, name='query_prompt_text'),
    path('updateMemory', views.update_memory, name='updateMemory'),
    path('instructionsset', views.instructions_set, name='instructions_set'),  
    path('save-or-edit-instructiontheme/', views.save_or_edit_instructiontheme, name='save_or_edit_instructiontheme'),
    path('instructionstheme', views.instructions_theme, name='instructions_theme'),  
    path('save-or-edit-instruction/', views.save_or_edit_instruction, name='save_or_edit_instruction'),
    path('delete-instruction/', views.delete_instruction, name='delete_instruction'),
    path('delete-instruction-theme/', views.delete_instruction_theme, name='delete_instruction_theme'),
    path('clear_memory/', views.clear_memory, name='clear_memory'),
    path('setting_page/', views.setting_page, name='setting_page'),
    path('save_claude_api/', views.save_claude_api, name='save_claude_api'),
    path('save_openai_api/', views.save_openai_api, name='save_openai_api'),
    path('export-themes/', views.export_themes, name='export_themes'),
    path('import-themes/', views.import_themes, name='import_themes'),
    path('export-instructions/', views.export_instructions, name='export_instructions'),
    path('import-instructions/', views.import_instructions, name='import_instructions'),
]