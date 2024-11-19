# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import base64


class ControlVales(models.Model):
    _name = 'control.vales'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del documento',
        default='New',
        required=True,
        copy=False
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('sent', 'Enviado'),
            ('partially_paid', 'Parcialmente pagado'),
            ('fully_paid', 'Totalmente pagado'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    proveedor = fields.Many2one(
        'res.partner',
        string='Proveedor',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True
    )
    amount_total_vales = fields.Monetary(
        string='Total de vales',
        readonly=True,
        copy=False,
        compute='_amount_vales',
    )
    payment_ids = fields.One2many(
        'account.payment',
        'control_vales_id',
        string="Payment Line",
        copy=False,
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    apply_voucher = fields.Boolean(related="company_id.apply_voucher")

    def action_sent(self):
        ir_actions_report_sudo = self.env['ir.actions.report'].sudo()
        statement_report_action = self.env.ref('xma_pos_voucher_redemption.action_report_vales')
        statement_report = statement_report_action.sudo()
        content, _content_type = ir_actions_report_sudo._render_qweb_pdf(statement_report, res_ids=self.ids)
        name = self.name
        attachment = self.env['ir.attachment'].create({
            'name': _("%s.pdf", name),
            'type': 'binary',
            'mimetype': 'application/pdf',
            'raw': content,
            'res_model': self._name,
            'res_id': self.id,
        })
        client = {
            'email': self.proveedor.email,
            'name': self.proveedor.name
        }
        mess = "<p>Hola %s,<br/>Te hacemos entrega del reporte de vales: %s. </p>"
        message = _(mess) % (client['name'], name)
        mail_values = {
            'subject': _('Reporte %s', name),
            'body_html': message,
            'author_id': self.env.user.partner_id.id,
            'email_from': self.env.company.email or self.env.user.email_formatted,
            'email_to': client['email'],
            'attachment_ids': [(4, attachment.id)],
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        self.state = 'sent'

    def action_draft(self):
        self.state = 'draft'

    @api.depends('payment_ids.amount_signed')
    def _amount_vales(self):
        for vales in self:
            amount_total_vales = 0.0
            for line in vales.payment_ids:
                amount_total_vales += line.amount_signed
            vales.update({
                'amount_total_vales': amount_total_vales,
            })

    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
            vals['name']=self.env['ir.sequence'].next_by_code('control.vales') or 'New'
        result = super(ControlVales, self).create(vals)
        return result


class CajeoVales(models.Model):
    _name = 'cajeo.vales'

    name = fields.Char(
        string='Folio del vale',
        required=True,
        copy=False,
        readonly=True,
    )
