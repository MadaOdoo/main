odoo.define('xma_pos_voucher_redemption.PartnerListScreen', function (require) {
    'use strict';

    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
    const Registries = require('point_of_sale.Registries');
    const { isConnectionError } = require('point_of_sale.utils');

    const PosPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {
            async saveChanges(event) {
                let changes = event.detail.processedChanges;
                if(!changes.name.length || !changes.l10n_mx_edi_curp.length || !changes.mobile.length){
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Es necesario tener lleno los campos de nombre, curp y celular en contacto.'),
                    })
                    return false;
                }
                try {
                    let l10n_mx_edi_curp = changes.l10n_mx_edi_curp != undefined
                    if(l10n_mx_edi_curp){
                        let partner_id = changes.id
                        l10n_mx_edi_curp = changes.l10n_mx_edi_curp.toUpperCase()
                        if(l10n_mx_edi_curp.length > 0){
                            let result = await this.rpc({
                                model: 'res.partner',
                                method: 'validar_curp',
                                args: [l10n_mx_edi_curp,partner_id],
                            });
                            if(result){
                                await this.showPopup('ModalDialogWarningPopup', {
                                    title: this.env._t('¡ADVERTENCIA!'),
                                    body1: this.env._t('Ya existe un cliente con esta CURP.'),
                                })
                                return false;
                            }
                        }
                    }
                } catch (error) {
                    if (isConnectionError(error)) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Unable to save changes.'),
                        });
                    } else {
                        throw error;
                    }
                }
                super.saveChanges(event);
            }
        };

    Registries.Component.extend(PartnerListScreen, PosPartnerListScreen);

    return PartnerListScreen;
});
