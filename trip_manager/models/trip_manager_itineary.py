# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class TripManagerItineary(models.Model):
    """Stores master records for itinerary days linked to a trip package,
    capturing the day number, destinations visited, activity description,
    and suggested hotel per day, forming the day-by-day tour plan."""
    
    _name = 'trip.manager.itineary'
    _description = 'A central registry of trip itinearies related to packages'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    day_number = fields.Integer(string='Day', required=True, default=1)    
    description = fields.Html(string='Description', required=True)
    no_of_days = fields.Integer(string='No Of Days', related='package_id.no_of_day', store=True)
    actual_date = fields.Date(string='Date', compute='_compute_actual_date')
    destination_domain = fields.Char(compute='_compute_destination_domain')

    package_destination_city_id = fields.Many2one('trip.manager.city', related='package_id.destination_city_id', 
                                                  string='Package Destination City', store=True)
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
            
    def _get_actual_date(self, start_date):
        """Returns the actual travel date for this itinerary day given a
        tour start date, or False if either is missing."""

        self.ensure_one()
        if start_date and self.day_number:
            return start_date + timedelta(days=self.day_number - 1)
        return False

    def _compute_actual_date(self):
            """Derives a display date from the tour start date passed in
            context, used when itineraries are shown inside an enquiry option."""

            start = self.env.context.get('tour_start_date') or self.env.context.get('default_tour_start_date')
            start = fields.Date.from_string(start) if start else False
            for rec in self:
                rec.actual_date = rec._get_actual_date(start)
                
    @api.depends('package_destination_city_id')
    def _compute_destination_domain(self):
        for rec in self:
            if rec.package_destination_city_id:
                rec.destination_domain = str([('city_ids', 'in', rec.package_destination_city_id.id)])
            else:
                rec.destination_domain = str([])
