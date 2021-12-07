# Copyright 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def populate_stage_from_old_state(env):
    if column_exists(env.cr, "res_partner", "state"):
        stages = env["res.partner.stage"].search([])
        for stage in stages:
            _logger.info(
                "Migration: populate %s stage_id from pre-existing state %s...",
                stage.name,
                stage.state,
            )
            env.cr.execute(
                """
                UPDATE res_partner
                SET stage_id = %(id)s, state = %(state)s
                WHERE old_state = %(state)s
                """,
                {"id": stage.id, "state": stage.state},
            )


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    populate_stage_from_old_state(env)
