# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerVehicle(models.Model):
    """Stores master records for travel vehicles used in tour transportation,
    covering both land vehicles (Sedan, SUV, Tempo Traveller, Bus) and water
    vessels (Houseboat, Speed Boat, Ferry), along with pricing details such as
    rent per day, driver charge, extra km rate, and seating capacity."""
    
    _name = 'trip.manager.vehicle'
    _description = 'A central registry of vehicles'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Vehicle Name', required=True)
    vehicle_number = fields.Char(string='Vehicle Number')
    vehicle_type = fields.Selection([
        ('sedan',           'Sedan (1–4 Pax)'),
        ('suv',             'SUV (5–7 Pax)'),
        ('muv',             'MUV (6–8 Pax)'),
        ('tempo_traveller', 'Tempo Traveller (9–26 Pax)'),
        ('mini_bus',        'Mini Bus (20–35 Pax)'),
        ('bus',             'Bus (35+ Pax)'),
        ('houseboat',    'Houseboat'),
        ('speed_boat',   'Speed Boat'),
        ('ferry',        'Ferry'),
        ('cruise',       'Cruise'),
        ('shikara',      'Shikara'),
    ], string='Vehicle Type')
    active = fields.Boolean(string='Active', default=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    rent_per_day = fields.Monetary(string='Rent / Day',        currency_field='currency_id')
    included_km_per_day = fields.Integer(string='Included KM / Day')
    extra_km_rate = fields.Monetary(string='Extra KM Rate', currency_field='currency_id')
    boarding_point = fields.Char(string='Boarding Point')
    drop_point = fields.Char(string='Drop Point')    
    owner_id = fields.Many2one('res.partner', string='Owner / Operator')
