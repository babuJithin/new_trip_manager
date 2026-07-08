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
    tour_end_date = fields.Date(related='enquiry_id.tour_end_date', string='Tour End Date', store=True)

    total_accomodation_cost = fields.Monetary(string='Total Trip Cost', 
                                            compute='_compute_total_accomodation_cost', store=True, currency_field='currency_id')
    total_transport_cost = fields.Monetary(string='Total Transport Cost', 
                                        compute='_compute_total_transport_cost', store=True, currency_field='currency_id')
    total_addon_cost = fields.Monetary(string='Additional Cost', compute='_compute_total_addon_cost', 
                                    store=True, currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True, 
                                currency_field='currency_id')
    margin_surplus = fields.Float(string='Margin (%)', digits=(16, 2), default=0.0)
    min_selling_rate = fields.Monetary(string='Minimum Selling Rate',compute='_compute_min_selling_rate', 
                                       store=True, currency_field='currency_id')
    selling_rate = fields.Monetary(string='Selling Rate', compute='_compute_selling_rate', store=True, 
                                   readonly=False, currency_field='currency_id')
    profit_amount = fields.Monetary(string='Profit', compute='_compute_profit', store=True, currency_field='currency_id')
    profit_percentage = fields.Float(string='Profit (%)', compute='_compute_profit', store=True, digits=(16, 2))
    flight_total = fields.Monetary(string='Flight Total', compute='_compute_flight_total', store=True)
    is_selected = fields.Boolean(string='Selected', default=False, copy=False,
                             help='The package option chosen by the customer. '
                                  'Exactly one option must be selected before confirmation.')
    
    flight_line_ids = fields.One2many('trip.manager.flight.line', 'option_id', string='Flights')
    enquiry_id   = fields.Many2one('trip.manager.enquiry', ondelete='cascade')
    package_id = fields.Many2one(related='enquiry_id.package_id', string='Package', store=True)
    booking_line_ids   = fields.One2many('trip.manager.booking.line', 'option_id', string='Booking Lines')
    transport_line_ids = fields.One2many('trip.manager.booking.transport', 'option_id', 
                                         string='Transportation')
    addon_ids = fields.One2many('trip.manager.enquiry.addon', 'option_id', string='Inclusions')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    package_itineary_ids = fields.One2many(related='package_id.itineary_ids', string='Itinerary Overview')
        
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('flight_line_ids.total')
    def _compute_flight_total(self):
        for option in self:
            option.flight_total = sum(option.flight_line_ids.mapped('total'))
            
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
        """Overrides default_get to pre-populate accommodation lines and entry
        ticket addons from the selected package's itinerary when a new option
        is created. Computes actual travel dates per day based on the tour
        start date. Accommodation lines are limited to the package's number
        of nights, so no line is created for the checkout day. Entry ticket
        addons are auto-fetched from destinations that have entry tickets
        enabled."""

        defaults = super().default_get(fields_list)
        package_id = (defaults.get('package_id') or self.env.context.get('default_package_id'))
        if package_id:
            package = self.env['trip.manager.package'].browse(package_id)
            start_date = defaults.get('tour_start_date') or \
                self.env.context.get('default_tour_start_date')
            if start_date:
                start_date = fields.Date.from_string(start_date)

            acc_lines = []
            addon_lines = []
            itineraries = package.itineary_ids.sorted('day_number')
            total_days = len(itineraries)
            no_of_nights = package.no_of_night or (total_days - 1 if total_days else 0)

            entry_ticket_category = self.env.ref(
                'trip_manager.addon_category_entry_ticket',raise_if_not_found=False)
            seen_destinations = set()

            for index, itineary in enumerate(itineraries):
                actual_date = itineary._get_actual_date(start_date)
                if index < no_of_nights:
                    acc_lines.append((0, 0, {
                        'itineary_id': itineary.id,
                        'actual_date': actual_date,
                        'destination_ids': [(6, 0, itineary.destination_ids.ids)],
                    }))
                for destination in itineary.destination_ids:
                    if destination.id in seen_destinations:
                        continue
                    if destination.has_entry_ticket and destination.entry_ticket_price:
                        addon_lines.append((0, 0, {
                            'category_id': entry_ticket_category.id if entry_ticket_category else False,
                            'description': destination.name,
                            'cost': destination.entry_ticket_price,
                        }))
                    seen_destinations.add(destination.id)

            defaults['booking_line_ids'] = acc_lines
            if addon_lines:
                defaults['addon_ids'] = addon_lines
        return defaults
        
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
        """Ensures no duplicate package category exists for the same enquiry,
        preventing two Standard or two Deluxe options from being created"""
        
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
                
    @api.depends('total_amount', 'margin_surplus')
    def _compute_min_selling_rate(self):
        """Computes the minimum selling rate by applying the margin
        percentage on top of the total net cost. With margin at 0,
        the minimum selling rate equals the total cost."""

        for rec in self:
            rec.min_selling_rate = rec.total_amount * (1 + (rec.margin_surplus or 0.0) / 100)

    @api.depends('min_selling_rate')
    def _compute_selling_rate(self):
        """Defaults the selling rate to the minimum selling rate whenever
        the margin or total cost changes. Editable (readonly=False), so
        the agent can manually override it with a custom rate."""

        for rec in self:
            rec.selling_rate = rec.min_selling_rate

    @api.depends('selling_rate', 'total_amount')
    def _compute_profit(self):
        """Computes profit (selling rate - total cost) and profit
        percentage relative to the selling rate."""

        for rec in self:
            rec.profit_amount = rec.selling_rate - rec.total_amount
            rec.profit_percentage = (
                (rec.profit_amount / rec.selling_rate) * 100
                if rec.selling_rate else 0.0
            )
