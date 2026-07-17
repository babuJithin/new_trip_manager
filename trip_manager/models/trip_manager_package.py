# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class TripManagerPackage(models.Model):
    """Stores master records for travel packages defining the tour structure,
    including itinerary days, inclusions, exclusions, cancellation policy,
    terms, visa fee, margin, and destination city, serving as the template
    from which customer enquiry options are generated."""
    
    _name = 'trip.manager.package'
    _description = 'A central registry of trip packages'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Pckage Name', required=True )
    image = fields.Image(string="Image", max_width=512, max_height=512)
    from_city = fields.Char(string='From City', required=True)
    no_of_day = fields.Integer(string='No Of Day', required=True)
    included_items = fields.Html(string="Included")
    excluded_items = fields.Html(string="Excluded")
    cancellation_policy = fields.Html(string="Cancellation Policy")
    terms_and_condition = fields.Html(string="Terms & Conditions")
    package_category = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International')
    ], string='Package category')
    margin_surplus = fields.Float(string='Margin Surplus (%)')
    visa_fee = fields.Monetary(string="Visa Fee", currency_field='currency_id')
    related_hotels_count = fields.Integer(string="Hotel Count", compute='_compute_related_hotels_count')
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    destination_city_id = fields.Many2one('trip.manager.city', string='Destination City')
    itineary_ids = fields.One2many('trip.manager.itineary','package_id', string="Itinearies")
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('destination_city_id', 'itineary_ids.hotel_id')
    def _compute_related_hotels_count(self):
        """Computes the count of hotels available in the package's destination city,
        displayed as a smart button on the package form for quick reference."""
        
        for rec in self:
            if rec.destination_city_id:
                city_hotels = self.env['trip.manager.hotel'].search([
                    ('city_ids', 'in', rec.destination_city_id.id)
                ])
                rec.related_hotels_count = len(city_hotels)
            else:
                rec.related_hotels_count = 0

    def action_open_related_hotels(self):
        """Opens a filtered list view of all hotels linked to the package's
        destination city, triggered from the smart button on the package form."""
        self.ensure_one()
        if self.destination_city_id:
            city_hotels = self.env['trip.manager.hotel'].search([
                ('city_ids', 'in', self.destination_city_id.id)
            ])
            hotel_ids = city_hotels.ids
        else:
            hotel_ids = []
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hotels',
            'res_model': 'trip.manager.hotel',
            'view_mode': 'list,form',
            'domain': [('id', 'in', hotel_ids)],
        }
