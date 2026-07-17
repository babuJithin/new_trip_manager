# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta

import logging

_logger = logging.getLogger(__name__)


class TripManagerEnquiryOption(models.Model):
    """Represents a single package tier option (Standard, Deluxe, Premium, or Luxury)
    for a customer enquiry, holding accommodation, transportation, and add-on lines
    along with computed cost totals presented as a quotation to the customer."""
    
    _name = 'trip.manager.enquiry.option'
    _description = 'Package type option for a customer enquiry'
    
    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    package_category = fields.Selection([
        ('standard', 'Standard'),
        ('deluxe',   'Deluxe'),
        ('premium', 'Premium'),
        ('luxury',   'Luxury'),
    ], string='Package Category', required=True, store=True)
    tour_start_date = fields.Date(related='enquiry_id.tour_start_date', string='Tour Start Date', store=True)
    total_accomodation_cost = fields.Monetary(string='Total Trip Cost', 
                                            compute='_compute_total_accomodation_cost', store=True, currency_field='currency_id')
    total_transport_cost = fields.Monetary(string='Total Transport Cost', 
                                        compute='_compute_total_transport_cost', store=True, currency_field='currency_id')
    total_addon_cost = fields.Monetary(string='Additional Cost', compute='_compute_total_addon_cost', 
                                    store=True, currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True, 
                                currency_field='currency_id')
    
    enquiry_id   = fields.Many2one('trip.manager.enquiry', ondelete='cascade')
    package_id = fields.Many2one(related='enquiry_id.package_id', string='Package', store=True)
    booking_line_ids   = fields.One2many('trip.manager.booking.line', 'option_id', string='Booking Lines')
    transport_line_ids = fields.One2many('trip.manager.booking.transport', 'option_id', 
                                         string='Transportation')
    addon_ids = fields.One2many('trip.manager.enquiry.addon', 'option_id', string='Inclusions')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
        
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('addon_ids.cost')
    def _compute_total_addon_cost(self):
        """Computes the total cost of all add-on inclusions such as
        entry tickets, guides, and activities for this option."""
        
        for rec in self:
            rec.total_addon_cost = sum(rec.addon_ids.mapped('cost'))
                
    @api.depends('transport_line_ids.total_transport_cost')
    def _compute_total_transport_cost(self):
        """Computes the total transportation cost by summing
        all daily vehicle transport costs for this option."""
        
        for rec in self:
            rec.total_transport_cost = sum(
                rec.transport_line_ids.mapped('total_transport_cost')
            )
            
    @api.depends('booking_line_ids.total_line_cost')
    def _compute_total_accomodation_cost(self):
        """Computes the total accommodation cost by summing
        all daily hotel booking line costs for this option."""
        
        for rec in self:
            rec.total_accomodation_cost = sum(rec.booking_line_ids.mapped('total_line_cost'))
            
    @api.depends('total_accomodation_cost', 'total_transport_cost', 'total_addon_cost')
    def _compute_total_amount(self):
        """Computes the grand total by summing accommodation,
        transportation, and add-on costs for this option."""
        
        for rec in self:
            rec.total_amount = rec.total_accomodation_cost + rec.total_transport_cost + rec.total_addon_cost
            
    @api.model
    def default_get(self, fields_list):
        """Overrides default_get to pre-populate accommodation and transportation lines
        from the selected package's itinerary when a new option is created.
        Computes actual travel dates per day based on the tour start date."""
        
        defaults = super().default_get(fields_list)
        package_id = (defaults.get('package_id') or self.env.context.get('default_package_id'))
        if package_id:
            package = self.env['trip.manager.package'].browse(package_id)
            start_date = defaults.get('tour_start_date') or \
             self.env.context.get('default_tour_start_date')
            if start_date:
                start_date = fields.Date.from_string(start_date)
            acc_lines = []
            trn_lines = []
            for itineary in package.itineary_ids.sorted('day_number'):
                day_num = itineary.day_number
                actual_date = False
                if start_date and day_num:
                    actual_date = start_date + timedelta(days=day_num - 1)
                acc_lines.append((0, 0, {
                    'itineary_id': itineary.id,
                    'day_number': day_num,      
                    'actual_date': actual_date, 
                    'package_category': defaults.get('package_category') or
                    self.env.context.get('default_package_category'),
                    'destination_ids': [(6,0, itineary.destination_ids.ids)],
                    'itineary_description': itineary.description,
                }))
                trn_lines.append((0, 0, {
                    'itineary_id': itineary.id,
                    'day_number': day_num,      
                    'actual_date': actual_date, 
                }))
            defaults['booking_line_ids']   = acc_lines
            defaults['transport_line_ids'] = trn_lines
        return defaults
        
    @api.constrains('enquiry_id', 'package_category')
    def _check_unique_package_category(self):
        """Ensures no duplicate package category exists for the same enquiry,
        preventing two Standard or two Deluxe options from being created."""
        
        for rec in self:
            duplicate = self.search([
                ('enquiry_id', '=', rec.enquiry_id.id),
                ('package_category', '=', rec.package_category),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    f'Package category "{rec.package_category}" already exists for this enquiry!'
                )
                
    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to sync the package category from the option
        down to all its booking lines after creation."""
        
        records = super().create(vals_list)
        for rec in records:
            if rec.package_category:
                for line in rec.booking_line_ids:
                    line.package_category = rec.package_category
        return records
    
    @api.constrains('package_category', 'enquiry_id')
    def _check_unique_category(self):
        """Secondary uniqueness check ensuring only one option per package
        category is allowed per enquiry. Raises a ValidationError on violation."""
        
        for rec in self:
            if not rec.package_category or not rec.enquiry_id:
                continue
            domain = [
                ('id', '!=', rec.id),
                ('enquiry_id', '=', rec.enquiry_id.id),
                ('package_category', '=', rec.package_category)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    "Only one %s package is allowed per enquiry!" % rec.package_category
                )
                
# ------------------------------------------------------------------------------
#   MARK: UTILITY METHODS
# ------------------------------------------------------------------------------
    def action_debug_booking_lines(self):
        """Debug utility that logs booking line and itinerary details
        for this option to the server log. Used during development
        to verify hotel and itinerary ID matching."""
        
        for opt in self:
            for bl in opt.booking_line_ids:
                _logger.warning(
                    "OPTION: %s | BL itineary_id: %s (id=%s) | hotel: %s",
                    opt.package_category,
                    bl.itineary_id.name if bl.itineary_id else 'None',
                    bl.itineary_id.id,
                    bl.hotel_id.name if bl.hotel_id else 'No hotel'
                )
            for day in opt.package_id.itineary_ids:
                _logger.warning(
                    "PACKAGE itineary day_number: %s id: %s",
                    day.day_number, day.id
                )