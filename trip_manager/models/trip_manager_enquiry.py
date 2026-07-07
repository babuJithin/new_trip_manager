# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class TripManagerEnquiry(models.Model):
    """Manages customer tour enquiries, capturing travel dates, passenger count,
        destination, package selection, and multiple package tier options presented
        as a quotation. Tracks the enquiry lifecycle from Draft to Estimate to Confirmed."""
        
    _name = 'trip.manager.enquiry'
    _description = 'Manages customer tour enquiries and package recomendations'
    _rec_name = 'customer_id'
    _order = 'enquiry_priority desc'  

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string="Order Reference", required=True, copy=False, readonly=False, 
                       index='trigram', default=lambda self: _('New'))
    tour_start_date = fields.Date(string="Start date", required=True)
    tour_end_date = fields.Date(string="End date", required=True)
    no_of_day = fields.Integer(string='No Of Day', compute='_compute_no_of_day', required=True)
    no_of_child = fields.Integer(string="Number of Child", required=True, default=0)
    no_of_adult = fields.Integer(string="Number of Adult", required=True)
    no_of_pax = fields.Integer(string="Number of Pax", compute='_compute_no_of_pax')
    enquiry_priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High')
    ], string="Priority")
    follow_up_date = fields.Date(string="Follow-up Date", required=True)
    state = fields.Selection([
        ('draft',     'Draft'),
        ('send',  'Send'),
        ('confirmed', 'Confirmed'),
        ('cancel',    'Cancelled'),
    ], string='Status', default='draft')
    package_type= fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International')
    ], string='Package Type', default='domestic')
    package_no_of_day   = fields.Integer(related='package_id.no_of_day', string='No Of Days')
    package_visa_fee    = fields.Monetary(related='package_id.visa_fee', string='Visa Fee',      
                                          currency_field='currency_id')
    package_included    = fields.Html(related='package_id.included_items', string='Included')
    package_excluded    = fields.Html(related='package_id.excluded_items', string='Excluded')
    package_cancellation= fields.Html(related='package_id.cancellation_policy', string='Cancellation Policy')
    package_terms       = fields.Html(related='package_id.terms_and_condition', string='Terms & Conditions')
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, index=True)
    destination_city_id = fields.Many2one('trip.manager.city', string='Destination City')
    package_id = fields.Many2one('trip.manager.package',  string='Packages', 
                                 domain="[('destination_city_id', '=', destination_city_id), ('no_of_day', '=', no_of_day)]")
    option_ids = fields.One2many('trip.manager.enquiry.option', 'enquiry_id', string='Options')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('tour_start_date', 'tour_end_date')
    def _compute_no_of_day(self):
        """Computes the total number of tour days from
        start to end date. Returns 0 if either date is missing."""
        
        for rec in self:
            if rec.tour_start_date and rec.tour_end_date:
                delta = rec.tour_end_date - rec.tour_start_date
                rec.no_of_day = delta.days  + 1
            else:
                rec.no_of_day = 0
                
    @api.constrains('no_of_adult')
    def _check_no_of_adult(self):
        """Ensures at least one adult is present"""
        
        for rec in self:
            if rec.no_of_adult <= 0:
                raise ValidationError(_("Number of adults must be at least 1."))
                
    @api.depends('no_of_adult', 'no_of_child')
    def _compute_no_of_pax(self):
        """Computes the total no of Pax from number of adults and 
        number of childs"""
        
        self.no_of_pax = self.no_of_adult+self.no_of_child
        
    @api.onchange('destination_city_id')
    def _onchange_destination_city_id(self):
        """Resets package and options when destination city changes,
        and filters the package domain to show only packages for the
        selected city."""
        
        self.package_id = False
        self.option_ids = [(5, 0, 0)]
        return {
            'domain': {
                'package_id': [('destination_city_id', '=', self.destination_city_id.id)]
            }
        }
        
    @api.onchange('tour_start_date', 'tour_end_date')
    def _onchange_tour_dates(self):
        """Shows an inline warning when tour dates are invalid,
        giving the user immediate feedback before saving."""
        
        today = fields.Date.today()
        if self.tour_start_date and self.tour_start_date < today:
            return {
                'warning': {
                    'title': 'Invalid Start Date',
                    'message': 'Tour start date cannot be in the past.'
                }
            }
        if self.tour_end_date and self.tour_start_date and self.tour_end_date < self.tour_start_date:
            return {
                'warning': {
                    'title': 'Invalid End Date',
                    'message': 'Tour end date cannot be before the start date.'
                }
            }
              
    @api.onchange('follow_up_date')
    def _onchange_follow_up_date(self):
        """Shows an inline warning when the follow-up date is invalid."""

        if not self.follow_up_date:
            return
        if self.follow_up_date < fields.Date.today():
            return {
                'warning': {
                    'title': 'Invalid Follow-up Date',
                    'message': 'Follow-up date cannot be in the past.'
                }
            }
        if self.tour_start_date and self.follow_up_date >= self.tour_start_date:
            return {
                'warning': {
                    'title': 'Invalid Follow-up Date',
                    'message': 'Follow-up date should be before the tour start date.'
                }
            }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _("New")) == _("New"):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'trip.manager.enquiry') or _("New")
        return super().create(vals_list)
    # ------------------------------------------------------------------------------
    #   MARK: BUTTON METHODS
    # ------------------------------------------------------------------------------
    def action_set_send(self):
        """Moves the enquiry to Send state, indicating that a
        quotation has been prepared for the customer."""
        
        self.ensure_one()
        self.state = 'send'

    def action_confirm(self):
        """Confirms the enquiry, indicating the customer has accepted
        the quotation and the booking is proceeding."""
        
        self.ensure_one()
        self.state = 'confirmed'
        
    def action_cancel(self):
        """Cancels the enquiry. cancelled enquiry can be reopened via Reset to Draft."""

        self.ensure_one()
        self.state = 'cancel'

    def action_reset_draft(self):
        """Resets the enquiry back to Draft state, allowing
        modifications to be made before re-estimating."""
        
        self.ensure_one()
        self.state = 'draft'
        
    def action_print_quotation(self):
        """Triggers the Tour Package Quotation PDF report for this enquiry.
        Flushes pending ORM writes before rendering to ensure all cost
        totals and hotel selections are up to date in the report."""
        
        self.ensure_one()
        self.env.flush_all()
        for opt in self.option_ids:
            for line in opt.booking_line_ids:
                _logger.warning(
                    "PRINT DEBUG -> Day:%s Hotel:%s",
                    line.day_number,
                    line.hotel_id.name if line.hotel_id else 'NONE'
                )
        return self.env.ref(
            'trip_manager.action_report_trip_enquiry_quotation'
        ).report_action(self)
        
