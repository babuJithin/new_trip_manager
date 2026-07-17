# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta

import logging

_logger = logging.getLogger(__name__)


class TripManagerBookingLine(models.Model):
    """Represents a single day's itinerary line for a customer enquiry,
    capturing dynamic booking details such as accommodation, hotel selection,
    room type, and date — derived from the selected trip package template."""   
    
    _name = 'trip.manager.booking.line'
    _description = 'Enquiry Booking Line'
    _order = 'day_number asc'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    package_category = fields.Selection([
        ('standard', 'Standard'),
        ('deluxe',   'Deluxe'),
        ('premium', 'Premium'),
        ('luxury',   'Luxury'),
    ], string='Package Category')
    tour_start_date = fields.Date(related='option_id.enquiry_id.tour_start_date', string='Tour Start Date', 
                                  store=True)
    actual_date = fields.Date(string='Date')
    day_number = fields.Integer(store=True, string='Day')
    itineary_description = fields.Html(string='Description', store=True)
    star_rating = fields.Selection(related='hotel_id.star_rating', string='Star Rating')
    has_breakfast = fields.Boolean(related='hotel_id.has_breakfast', string='Breakfast Included')
    check_in = fields.Float(related='hotel_id.check_in', string='Check-in')
    check_out = fields.Float(related='hotel_id.check_out', string='Check-out')
    extra_bed_available = fields.Boolean(related='hotel_id.extra_bed_available', string='Extra Bed Available')
    extra_bed_price = fields.Monetary(related='hotel_id.extra_bed_price', string='Extra Bed Price', 
                                      currency_field='currency_id')
    room_rate = fields.Monetary(related='room_type_id.room_rate', string='Room Rate', 
                                       currency_field='currency_id')
    max_occupancy = fields.Integer(related='room_type_id.max_occupancy', string='Max Occupancy')
    no_of_rooms = fields.Integer(string='No of Rooms', default=1)
    no_of_child = fields.Integer(related='enquiry_id.no_of_child', string='Childs')
    no_of_adult = fields.Integer(related='enquiry_id.no_of_adult', string='Adults')
    room_cost = fields.Monetary(string='Room Cost', compute='_compute_costs', store=True, 
                                currency_field='currency_id')
    no_of_extra_bed = fields.Integer(string='No of Extra Rooms', default=0)
    extra_bed_cost = fields.Monetary(string='Extra Bed Cost', compute='_compute_costs', store=True, 
                                     currency_field='currency_id')
    total_line_cost = fields.Monetary(string='Day Total', compute='_compute_costs', store=True, 
                                      currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', related='hotel_id.currency_id', string='Currency')
    hotel_id = fields.Many2one('trip.manager.hotel', string='Hotel', 
                               domain="[('id', 'in', available_hotel_ids)]")
    destination_ids = fields.Many2many('trip.manager.destination', string='Destinations')
    available_hotel_ids = fields.Many2many('trip.manager.hotel', compute='_compute_available_hotel_ids', 
                                           string='Available Hotels')
    room_type_id = fields.Many2one('trip.manager.hotel.room.type', string='Room Type', 
                                   domain="[('hotel_id', '=', hotel_id)]")
    option_id = fields.Many2one('trip.manager.enquiry.option', string='Option', required=True, 
                                ondelete='cascade')
    enquiry_id = fields.Many2one('trip.manager.enquiry', related='option_id.enquiry_id', 
                              store=True, string='Enquiry')
    package_id = fields.Many2one(related='enquiry_id.package_id', store=True, string='Package')
    itineary_id = fields.Many2one('trip.manager.itineary', string='Itinerary Day', 
                                  domain="[('package_id', '=', package_id)]")
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('room_rate', 'no_of_rooms', 'extra_bed_price', 'no_of_extra_bed')
    def _compute_costs(self):
        """Calculates room cost, extra bed cost, and total line cost
            based on room rate, number of rooms, extra bed price, and extra bed count."""
        
        for line in self:
            line.room_cost       = line.room_rate  * line.no_of_rooms
            line.extra_bed_cost  = line.extra_bed_price * line.no_of_extra_bed
            line.total_line_cost = line.room_cost + line.extra_bed_cost

    @api.onchange('itineary_id')
    def _onchange_itineary_id(self):
        """Resets hotel and room type selection when itinerary day changes,
           preventing stale values from carrying over to the new selection."""
           
        self.hotel_id = False
        self.room_type_id = False

                
    @api.onchange('hotel_id')
    def _onchange_hotel_id(self):
        """Resets room type when hotel changes, since room types
            are specific to each hotel."""
            
        self.room_type_id = False 
        
    @api.onchange('itineary_id')
    def _onchange_refresh_hotels(self):
        """Triggers recomputation of available hotels when the
            itinerary day changes, since hotels are filtered by destination."""
            
        for line in self:
            line._compute_available_hotel_ids()
            
    @api.onchange('option_id')
    def _onchange_option_id(self):
        """Syncs the package category from the parent option to this booking line,
            ensuring hotel filtering is aligned with the selected package tier."""
            
        for line in self:
            if line.option_id:
                line.package_category = line.option_id.package_category
                
    @api.onchange('itineary_id', 'tour_start_date')
    def _onchange_dates(self):
        """Computes the actual travel date for this line based on the tour start date
            and the day number derived from the selected itinerary day."""
            
        for rec in self:
            if rec.itineary_id:
                rec.day_number = rec.itineary_id.day_number

            if rec.tour_start_date and rec.day_number:
                rec.actual_date = rec.tour_start_date + timedelta(
                    days=rec.day_number - 1
                )
       
    @api.onchange('package_category')
    def _onchange_package_category(self):
        """Refreshes the available hotels list when package category changes,
            since hotels are filtered by star rating based on the category tier."""
            
        for line in self:
            line._compute_available_hotel_ids()     
                
    @api.depends('itineary_id', 'package_category', 'option_id')
    def _compute_available_hotel_ids(self):
        """Computes the list of hotels available for selection based on the
            destinations linked to the itinerary day and the package category tier.
            Hotels are filtered by city (derived from itinerary destinations)
            . If no starred hotels are foundfor the selected category, falls back to 
            all hotels in the destination city."""
    
        preferred_stars = {
            'standard': ['0', '1', '2'],
            'deluxe':   ['3'],
            'premium':  ['4'],
            'luxury':   ['5'],
        }
        for line in self:
            _logger.info("compute running for line %s", line.id)
            if not line.itineary_id:
                line.available_hotel_ids = False
                continue
            destinations = line.itineary_id.destination_ids
            city_ids = destinations.mapped('city_ids').ids
            _logger.info("CITY IDS: %s", city_ids)
            if not city_ids:
                line.available_hotel_ids = False
                continue
            category = line.package_category 
            _logger.info("CATEGORY: %s", category)
            stars = preferred_stars.get(category, [])
            domain = [('city_ids', 'in', city_ids)]
            if stars:
                hotels = self.env['trip.manager.hotel'].search(
                    domain + [('star_rating', 'in', stars)]
                )
                if not hotels:
                    hotels = self.env['trip.manager.hotel'].search(domain)
            else:
                hotels = self.env['trip.manager.hotel'].search(domain)
            _logger.info("HOTELS FOUND: %s", hotels.ids)
            line.available_hotel_ids = hotels
            
    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to ensure day_number is synced from the itinerary
            after record creation, since it may not be set via default_get."""
            
        records = super().create(vals_list)
        for rec in records:
            if rec.itineary_id:
                rec.day_number = rec.itineary_id.day_number
        return records

    def write(self, vals):
        """Overrides write to keep day_number in sync with the itinerary
            whenever the booking line is updated."""
            
        res = super().write(vals)
        for rec in self:
            if rec.itineary_id:
                rec.day_number = rec.itineary_id.day_number
        return res