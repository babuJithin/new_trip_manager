# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'TRIP MANAGER',
    'version': '19.0.1.0.0',
    'category': 'Operations',
    'sequence': 10,
    'author': 'Sreejith Vijayakumar',
    'summary': 'Helps to manage tour operations',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        
        'report/trip_manager_enquiry_report.xml',
        
        'views/report_trip_manager_enquiry.xml', 
        'views/trip_manager_addon_category_views.xml',
        'views/trip_manager_enquiry_option_views.xml',
        'views/trip_manager_enquiry_views.xml',
        'views/res_partner_views.xml',
        'views/trip_manager_vehicle_views.xml',
        'views/trip_manager_hotel_room_type_views.xml',
        'views/trip_manager_itineary_views.xml',
        'views/trip_manager_package_views.xml',
        'views/trip_manager_destination_category_views.xml',
        'views/trip_manager_activity_views.xml',
        'views/trip_manager_destination_views.xml',
        'views/trip_manager_hotel_views.xml',
        'views/trip_manager_city_views.xml',
        'views/trip_manager_menus.xml'
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
