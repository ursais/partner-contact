# Copyright 2021 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    api.Environment(cr, SUPERUSER_ID, {})
    query = """
    ALTER TABLE res_partner
    ADD COLUMN state_old VARCHAR
    """
    cr.execute(query)
    cr.execute("UPDATE res_partner SET state_old = state")


def post_init_hook(cr, registry):
    """Set default Stage on partners"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env["res.partner"]
    default_stage = Partner._get_default_stage_id()
    missing_stages = Partner.search([("stage_id", "=", False)])

    query = """
            UPDATE res_partner as prt SET stage_id = (
            SELECT id FROM res_partner_stage as ps WHERE ps.state = prt.state_old
            )
            """
    cr.execute(query)
    cr.execute("ALTER TABLE res_partner DROP COLUMN state_old")
    if default_stage and missing_stages:
        _logger.info("Init stage_id for %d partner records...", len(missing_stages))
        cr.execute(
            """
            UPDATE res_partner
            SET stage_id = %(id)s, state = %(state)s
            WHERE stage_id IS NULL
            """,
            {"id": default_stage.id, "state": default_stage.state},
        )
