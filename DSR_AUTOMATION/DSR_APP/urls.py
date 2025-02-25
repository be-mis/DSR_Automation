from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload-page'),


    path('validation', views.upload_validation, name='upload-validation'),
    path('comparison/<str:instance>/', views.comparison_view, name='comparison-function'),

    path('processdata/<str:instance>/', views.process_data, name='process-data'),
    # path('addsheets/<str:instance>/', views.add_sheets, name='add-sheets'),
    path('generated/<str:instance>/', views.render_processed_data, name='generated-page'),
    path('download/<str:instance>/', views.download_excel, name='download-excel'),
    # path('edit-item-code/<int:row_id>/<int:file_id>/', views.edit_item_code, name='edit-item-code'),
    # path('edit-bp-code/<int:row_id>/<int:file_id>/', views.edit_bp_code, name='edit-bp-code'),
    path('edit-field/<str:field_name>/<int:row_id>/<int:file_id>/', views.edit_field, name='edit_field'),


    # path('validate', views.validatedsr, name='validate-dsr'),
    path('displaydsr/<str:doc_date>/<str:doc_remarks>/<str:database_type>/', views.displayuploadeddsr, name='display-dsr'),
    # path('detailed/<str:doc_date>/<str:doc_remarks>/<str:database_type>/', views.detaileddsr, name='display-detailed-dsr'),

    path('data/', views.show_data, name='data'),
    path('delete/<str:instance>/', views.delete_data, name='delete-data'),

    path('delete-selected/', views.delete_selected, name='delete-selected'),

    # path('generated/<str:batch_id>/', views.generated_page, name='generated-page'),
    # path('delete/<str:batch_id>/', views.delete_data, name='delete-data'),

    path('fetch-remarks/', views.fetch_remarks, name='fetch-remarks'),

    path('input-info/<str:chain>/<str:original_name>/<str:database>/', views.input_info, name="input-info"),


    # path('validate/<str:instance>/', views.validate_dsr, name='validate-dsr'),
]
