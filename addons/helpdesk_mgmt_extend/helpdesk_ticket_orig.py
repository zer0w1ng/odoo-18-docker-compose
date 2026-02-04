# -*- coding: utf-8 -*-
###############################################
# (c) 2024 Regulus Berdin
###############################################
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTicketLine(models.Model):
    _name = "helpdesk.ticket.line"
    _order = 'create_date'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket')
    query = fields.Html()
    answer = fields.Html()
    # query = fields.Text()
    # answer = fields.Text()
    is_answerd = fields.Boolean()

    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket.line")],
        string="Attachments",
    )

    is_admin = fields.Boolean(related="ticket_id.is_admin")
    is_submitted = fields.Boolean()
    is_closed = fields.Boolean()


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update({
                'is_submitted': True,
            })
        res = super().create(vals_list)
        return res


    def write(self, vals):
        for _ticket in self:
            if vals.get("query"):
                self.is_submitted = True
            if vals.get("answer"):
                self.is_closed = True
        return super().write(vals)


    def action_submit(self):
        pass


    def action_answer(self):
        pass


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"
    

    def is_mananager(self):
        return self.env.user.has_group('helpdesk_mgmt.group_helpdesk_user_team') \
            or self.env.user.has_group('helpdesk_mgmt.group_helpdesk_user') \
            or self.env.user.has_group('helpdesk_mgmt.group_helpdesk_manager')


    def _get_default_partner_id(self):
        # if self.env.user.has_group('helpdesk_mgmt.group_helpdesk_user_team') \
        #     or self.env.user.has_group('helpdesk_mgmt.group_helpdesk_user') \
        #     or self.env.user.has_group('helpdesk_mgmt.group_helpdesk_manager'):
        if self.is_mananager():
            return False
        else:
            return self.env.user.partner_id.id


    partner_id = fields.Many2one(default=_get_default_partner_id)
    user_access = fields.Boolean(compute='_get_user_access')
    escalate_after = fields.Datetime('Auto-Escalate After', default=False)
    escalate = fields.Boolean(compute='_get_escalate', store=True)
    is_escalated = fields.Boolean('Escalated', tracking=True)
    description = fields.Html(required=False, sanitize_style=True)

    task_id = fields.Many2one(
        comodel_name="helpdesk.ticket.task",
        string="Issue",
        tracking=True,
        index=True,
        readonly=False,
    )

    name = fields.Char(related='task_id.name')
    help_link = fields.Char(related='task_id.help_link')
    help_label = fields.Char(related='task_id.help_label')
    help_url = fields.Html(related='task_id.help_url')
    is_link = fields.Boolean(compute='_get_is_link')

    tag_name = fields.Char(compute='_get_tag_name')

    timecard_id = fields.Many2one('ez.time.card', string='Time Card')
    timeoff_id = fields.Many2one('hr.leave', string='Time Off')
    payslip_id = fields.Many2one('hr.ph.payslip', string='Payslip')
    state = fields.Char(related='stage_id.name', store=True)
    is_admin = fields.Boolean(compute="_get_is_admin")
    is_submitted = fields.Boolean(compute="_get_is_submit")
    color = fields.Integer(compute="_get_color")

    line_ids = fields.One2many('helpdesk.ticket.line', 'ticket_id', 'Ticket Lines')


    @api.depends('help_link')
    def _get_is_link(self):
        for r in self:
            if r.help_link or r.task_id.help_label:
                 r.is_link = True
            else:
                 r.is_link = False
            # if (r.help_link or '')[:4] == 'http':
            #     r.is_link = True
            # else:
            #     r.is_link = False


    @api.depends('is_escalated')
    def _get_color(self):
        for r in self:
            r.color = r.is_escalated and 4 or 0


    @api.depends('line_ids','line_ids.is_submitted')
    def _get_is_submit(self):
        for ticket in self:
            is_submitted = False
            for r in ticket.line_ids:
                is_submitted = r.is_submitted
            ticket.is_submitted = is_submitted


    # def _get_is_admin2(self):
    #     for r in self:
    #         r.is_admin = False

    def _get_is_admin(self):
        is_admin = self.is_mananager()
        for r in self:
            r.is_admin = is_admin


    @api.depends("team_id")
    def _compute_user_id(self):
        for ticket in self:
            if ticket.team_id.user_id:
                super()._compute_user_id()
            else:
                ticket.user_id = ticket.task_id.assigned_id


    @api.depends('tag_ids', 'tag_ids.name')
    def _get_tag_name(self):
        for r in self:
            tag_names = [t.name for t in r.tag_ids]
            r.tag_name = " ".join(tag_names)


    @api.onchange('task_id')
    def oc_task_id(self):
        if not self.team_id:
            self.team_id = self.task_id.team_id.id
        #self.user_id = self.sudo().task_id.assigned_id.id
        self.category_id = self.sudo().task_id.category_id.id
        self.tag_ids = self.sudo().task_id.tag_ids.ids
        self.escalate_after = fields.Datetime.now() + relativedelta(hours=self.sudo().task_id.turn_around_time)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("task_id"):
                task_id = self.sudo().env["helpdesk.ticket.task"].browse([vals["task_id"]])
                vals['team_id'] = task_id.team_id.id
                vals['category_id'] = task_id.category_id.id
                vals['tag_ids'] = task_id.tag_ids.ids
                vals['escalate_after'] = fields.Datetime.now() + relativedelta(hours=task_id.turn_around_time)
        return super().create(vals_list)


    @api.depends('closed','unattended')
    def _get_escalate(self):
        for r in self:
            r.escalate = (not r.closed) and (not r.unattended)


    def action_escalate0(self):
        self.ensure_one()
        if not self.team_id.escalate_ids.ids:
            raise AccessError(_("No escalation email defined on Team."))
        self.action_escalate()


    def action_cancel(self):
        self.ensure_one()
        rec = self.env['helpdesk.ticket.stage'].search([('name','=','Cancelled')], limit=1)
        if rec:
            self.sudo().stage_id = rec.id


    def action_escalate(self):
        self.ensure_one()
        if self.escalate and (not self.is_escalated):
            self.is_escalated = True
            if self.team_id.escalate_ids.ids:
                template = self.env.ref('ez_custom_novare.helpdesk_ecalation_email_template')
                template.send_mail(self.id, force_send=True, email_layout_xmlid='mail.mail_notification_layout')
                _logger.debug("ESCALATE EMAIL: %s %s", self.name, template)


    def action_reset_escalate(self):
        self.ensure_one()
        if self.is_escalated:
            self.is_escalated = False
            self.escalate_after = fields.Datetime.now() + relativedelta(hours=self.sudo().task_id.turn_around_time)


    @api.depends('partner_id')
    def _get_user_access(self):
        for r in self:
            if not r.partner_id:
                r.user_access = False
            elif self.env.user.partner_id.id==r.partner_id.id:
                r.user_access = True
            else:
                r.user_access = False


    def check_escalate(self):
        now = fields.Datetime.to_string(fields.Datetime.now())
        recs = self.env['helpdesk.ticket'].search([
            ('escalate','=',True),
            ('is_escalated','=',False),
            ('escalate_after','<',now),
        ])
        _logger.debug("CHECK ESCALATE: %s", recs)
        for r in recs:
            r.action_escalate()


    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            res["stage_id"][1].update({
                'email_layout_xmlid': 'mail.mail_notification_layout'
            })
        return res


    def write(self, vals):
        for _ticket in self:
            if vals.get("stage_id"):
                stage = self.env['helpdesk.ticket.stage'].browse(vals.get("stage_id"))
                _logger.debug('WRITE: stage=%s %s', _ticket.stage_id.name, stage.name)
                if (not self.is_mananager()) and (_ticket.stage_id.name not in ('In Progress','New')):
                    raise AccessError(_("Access denied. Cannot change ticket stage."))
        return super().write(vals)


    def action_submit(self):
        self.ensure_one()
        if self.stage_id.name == 'New':
            rec = self.env['helpdesk.ticket.stage'].search([('name','=','In Progress')])
            if rec:
                self.sudo().stage_id = rec.id


    def action_save(self):
        pass


    def action_close(self):
        self.ensure_one()
        rec = self.env['helpdesk.ticket.stage'].search([('name','=','Done')])
        if rec:
            self.sudo().stage_id = rec.id



class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    escalate_ids = fields.Many2many('res.users', 
        'escalate_user_rel', 'ticket_id','user_id',                                     
        string="Escalate To") #, default=lambda self: self.env.ref("hr.group_hr_manager").users.ids)
    escalate_emails = fields.Char(compute='_get_escalate_email')

    @api.depends('escalate_ids')
    def _get_escalate_email(self):
        for r in self:
            r.escalate_emails = ','.join([app.partner_id.email for app in r.escalate_ids if '@' in (app.partner_id.email or '')])


# class HelpdeskTicketStage(models.Model):
#     _inherit = "helpdesk.ticket.stage"

#     escalate = fields.Boolean()

class Task(models.Model):
    _name = "helpdesk.ticket.task"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char()
    team_id = fields.Many2one('helpdesk.ticket.team', string='Team')
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags")
    assigned_id = fields.Many2one('res.users', string='Assigned POC')
    category_id = fields.Many2one('helpdesk.ticket.category', string='Category')
    turn_around_time = fields.Integer()
    help_link = fields.Char()
    help_label = fields.Char()
    help_url = fields.Html(compute="_get_help_url")
    

    @api.depends('help_link','help_label')
    def _get_help_url(self):
        for r in self:
            if r.help_link:
                if r.help_label:
                    label = r.help_label
                else:
                    label = r.help_link
                r.help_url = f'<a href="{r.help_link}">{label}</a>'
            else:
                r.help_url = r.help_label or ""



class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    task_ids = fields.One2many('helpdesk.ticket.task', 'team_id', 'Tasks')
