# Copyright (C) 2015 Forest and Biomass Romania
# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from stdnum.eu.vat import check_vies
except ImportError:
    _logger.debug("Cannot import check_vies method from python stdnum.")


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _parse_vies_address(self, address):
        res = {}
        if address and address != "---":
            address_parts = [x for x in address.split("\n") if x]
            if len(address_parts) > 1 and " " in address_parts[-1]:
                # Last line can be "ZipCode City"
                zip_city = address_parts.pop()
                res["zip"], res["city"] = zip_city.split(" ", 1)
            res["street"] = " ".join(address_parts)
        return res

    @api.model
    def _get_vies_data(self, vat, raise_if_fail=False):
        res = {}
        try:
            result = check_vies(vat)
        except Exception as e:
            _logger.warning("Failed to query VIES: %s", e)
            if raise_if_fail:
                raise UserError(
                    self.env._("Failed to query VIES.\nTechnical error: %s.", e)
                ) from None
            return res
        _logger.debug(result)
        # Update partner VAT
        if result.valid and result.name:
            res["vat"] = vat
            # Update partner name if listed on VIES
            if result.name != "---":
                res["name"] = result.name.upper()
            # Update partner address if listed on VIES
            res.update(self._parse_vies_address(result.address))
            # Get country by country code
            country = self.env["res.country"].search(
                [("code", "ilike", result.countryCode)]
            )
            if country:
                res["country_id"] = country[0].id
        return res

    def _vies_fetch_result(self):
        self.ensure_one()
        vat = (self.vat or "").strip().upper()
        if not vat or not self.is_company:
            return {}
        eu_group = self.env.ref("base.europe", raise_if_not_found=False)
        if not eu_group:
            return {}
        vat_country, _vat_number = self._split_vat(vat)
        vat_country = vat_country.upper()
        eu_countries = eu_group.country_ids.mapped("code")
        if vat_country and vat_country not in eu_countries:
            return {}
        return self._get_vies_data(vat)

    def _vies_populate(self):
        for partner in self:
            result = partner._vies_fetch_result()
            if result:
                # Context needed for compatibility with
                # partner_country_state_required, and to avoid a recursion
                # through the write override below.
                partner.with_context(
                    no_state_required=True, no_vies_populate=True
                ).write(result)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if not self.env.context.get("no_vies_populate"):
            partners._vies_populate()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if "vat" in vals and not self.env.context.get("no_vies_populate"):
            self._vies_populate()
        return res

    @api.onchange("vat")
    def vies_vat_change(self):
        for partner in self:
            result = partner._vies_fetch_result()
            if result:
                # Context needed for compatibility with
                # partner_country_state_required.
                partner.with_context(no_state_required=True).update(result)
