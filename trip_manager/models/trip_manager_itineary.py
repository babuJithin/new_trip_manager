# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TripManagerItineary(models.Model):
    """Stores master records for itinerary days linked to a trip package,
    capturing the day number, destinations visited, activity description,
    and suggested hotel per day, forming the day-by-day tour plan."""
    
    _name = 'trip.manager.itineary'
    _description = 'A central registry of trip itinearies related to packages'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    day_number = fields.Integer(string='Day', required=True)    
    description = fields.Html(string='Description', required=True)
    no_of_days = fields.Integer(string='No Of Days', related='package_id.no_of_day', store=True)
    
    package_id = fields.Many2one('trip.manager.package', string='Package Name')
    destination_ids = fields.Many2many('trip.manager.destination', string='Destinations')
    available_city_ids = fields.Many2many('trip.manager.city',compute='_compute_available_city_ids')
    hotel_id = fields.Many2one('trip.manager.hotel', string='Hotel')
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('destination_ids')
    def _compute_available_city_ids(self):
        """Computes the list of available cities by aggregating all cities
        linked to the selected destinations, used to filter hotels
        by location on the booking line."""
        
        for rec in self:
            rec.available_city_ids = rec.destination_ids.mapped('city_ids')
