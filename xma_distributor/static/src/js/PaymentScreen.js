odoo.define('xma_pos_voucher_redemption.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    // const { _t } = require('web.core');
    // const { useListener } = require('web.custom_hooks');

    const PosPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {
            async addNewPaymentLine({ detail: paymentMethod }) {
                // original function: click_paymentmethods
                var journal = {}
                if(paymentMethod.journal_id){
                    journal = this.env.pos.journal_by_id[paymentMethod.journal_id[0]]
                }
                if(journal.is_vale){
                    if(this.currentOrder.get_orderlines().length === 0){
                        await this.showPopup('ModalDialogWarningPopup', {
                            title: this.env._t('¡ADVERTENCIA!'),
                            body1: this.env._t('Debe haber al menos un producto en su pedido antes de seleccionar el metodo de pago de vale.'),
                        })
                        return false;
                    }
                    const line = this.paymentLines.find((line) => line.folio_de_vale != '' && line.folio_de_vale != null);
                    if(line != undefined && line.folio_de_vale.length >= 1) {
                        await this.showPopup('ModalDialogWarningPopup', {
                            title: this.env._t('¡ADVERTENCIA!'),
                            body1: this.env._t('Se encuentra un vale en uso '+line.folio_de_vale+', solo se puede canjear un vale por pedido.'),
                        })
                        return false;
                    }
                    let { confirmed, payload: code } = await this.showPopup('TextInputPopup', {
                        title: this.env._t('Introduzca el número de vale'),
                        startingValue: 'A-00003-0004',
                        placeholder: this.env._t('Ingrese el número de vale'),
                    });
                    if(confirmed){
                        if(code){
                            try {
                                const vale_api = await this.rpc({
                                    model: 'pos.order',
                                    method: 'validar_vale',
                                    args: [code, this.currentOrder.pos_session_id, this.currentOrder.partner.id, this.env.pos.config.token],
                                })
                                if(vale_api.id != undefined) {
                                    var monto_con_symbol = this.env.pos.format_currency(vale_api.monto);
                                    var monto_sin_symbol = this.env.pos.format_currency_no_symbol(vale_api.monto);
                                    // if(vale_api.estatus != 'porcobrar'){
                                    //     await this.showPopup('ModalDialogWarningPopup', {
                                    //         title: this.env._t('¡'+vale_api.nombreDistribuidora+'!'),
                                    //         body1: this.env._t('El vale con el folio '+vale_api.folio+' tiene un saldo de '+monto_con_symbol+' y se encuentra en estado '+vale_api.estatus+'.'),
                                    //     })
                                    //     return false;
                                    // }
                                    var monto_a_pagar = this.currentOrder.get_due() > 0 ? this.currentOrder.get_due() : 0
                                    if(vale_api.limiteDistribuidora > 0){
                                        monto_con_symbol = this.env.pos.format_currency(vale_api.limiteDistribuidora);
                                        const { confirmed, payload } = await this.showPopup('NumberPopup', {
                                            title: this.env._t('Limite de vale: '+monto_con_symbol),
                                        });
                                        if(confirmed) {
                                            if(payload > 0){
                                                if(payload <= vale_api.limiteDistribuidora){
                                                    if(payload <= monto_a_pagar){
                                                        monto_sin_symbol = this.env.pos.format_currency_no_symbol(payload);
                                                        monto_con_symbol = this.env.pos.format_currency(payload);
                                                    } else {
                                                        var _monto_a_pagar = this.env.pos.format_currency(monto_a_pagar);
                                                        await this.showPopup('ModalDialogWarningPopup', {
                                                            title: this.env._t('¡ADVERTENCIA!'),
                                                            body1: this.env._t('El monto ingresado debe ser menor o igual al monto a pagar, que es de'),
                                                            text1: this.env._t(_monto_a_pagar),
                                                        })
                                                        return false;
                                                    }
                                                } else {
                                                    await this.showPopup('ModalDialogWarningPopup', {
                                                        title: this.env._t('¡ADVERTENCIA!'),
                                                        body1: this.env._t('El monto ingresado no debe ser mayor al limite del vale, que es de '),
                                                        text1: this.env._t(monto_con_symbol),
                                                    })
                                                    return false;
                                                }
                                            } else {
                                                await this.showPopup('ModalDialogWarningPopup', {
                                                    title: this.env._t('¡ADVERTENCIA!'),
                                                    body1: this.env._t('El monto ingresado debe ser mayor a 0'),
                                                })
                                                return false;
                                            }
                                        } else {
                                            return false;
                                        }
                                    } else if(monto_sin_symbol == 0){
                                        await this.showPopup('ModalDialogWarningPopup', {
                                            title: this.env._t('¡'+vale_api.nombreDistribuidora+'!'),
                                            body1: this.env._t('El vale con el folio'),
                                            text1: this.env._t(vale_api.folio),
                                            body2: this.env._t('no cuenta con saldo, su monto es de'),
                                            text2: this.env._t(monto_con_symbol),
                                            body3: this.env._t('y se encuentra en estado'),
                                            text3: this.env._t(vale_api.estatus+'.'),
                                        })
                                        return false;
                                    }
                                    if(monto_sin_symbol <= monto_a_pagar){
                                        monto_a_pagar = monto_sin_symbol
                                    }
                                    await this.showPopup('ModalDialogSuccess', {
                                        title: this.env._t('¡'+vale_api.nombreDistribuidora+'!'),
                                        body1: this.env._t('El vale con el folio'),
                                        text1: this.env._t(vale_api.folio),
                                        body2: this.env._t('tiene un saldo de'),
                                        text2: this.env._t(monto_con_symbol),
                                        body3: this.env._t('y se encuentra en estado'),
                                        text3: this.env._t(vale_api.estatus),
                                        imageUrl: this.env._t(vale_api.firma),
                                    })
                                    let result = this.currentOrder.add_paymentline(paymentMethod)
                                    if(result){
                                        result.folio_de_vale = vale_api.folio
                                        this.currentOrder.folio_de_vale = vale_api.folio
                                        this.currentOrder.is_vale = true
                                        this.currentOrder.state_de_vale = 'Canjeado'
                                        this.currentOrder.distribuidora_id = vale_api.distribuidoraId
                                        let res = result.set_amount(monto_a_pagar);
                                        await this.rpc({
                                            model: 'pos.order',
                                            method: 'save_model_cajeo_vales',
                                            args: [vale_api],
                                        })
                                        NumberBuffer.reset();
                                        return true;
                                    } else {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('Error'),
                                            body: this.env._t('Ya hay un pago electrónico en curso.'),
                                        });
                                        return false;
                                    }
                                } else if(vale_api.estatus != 'porcobrar' && vale_api.estatus != undefined){
                                    await this.showPopup('ModalDialogWarningPopup', {
                                        title: this.env._t('¡'+vale_api.nombreDistribuidora+'!'),
                                        body1: this.env._t('El vale con el folio'),
                                        text1: this.env._t(vale_api.folio),
                                        body2: this.env._t('ya fue'),
                                        text2: this.env._t(vale_api.estatus+'.'),
                                    })
                                    return false;
                                } else {
                                    await this.showPopup('ErrorPopup', {
                                        title: this.env._t('¡'+vale_api.name+' '+vale_api.statusCode+'!'),
                                        body: this.env._t(vale_api.message+'.'),
                                    });
                                }
                            } catch (error) {
                                await this.showPopup('ErrorPopup', {
                                    title: this.env._t('¡ERROR!'),
                                    body: this.env._t('Prueba tu conexion de internet.'),
                                });
                                return false;
                            }
                        }
                    }
                } else {
                    super.addNewPaymentLine({ detail: paymentMethod });
                }
            }
            deletePaymentLine(event) {
                var self = this;
                const { cid } = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);

                // If a paymentline with a payment terminal linked to
                // it is removed, the terminal should get a cancel
                // request.
                if (['waiting', 'waitingCard', 'timeout'].includes(line.get_payment_status())) {
                    line.set_payment_status('waitingCancel');
                    line.payment_method.payment_terminal.send_payment_cancel(this.currentOrder, cid).then(function() {
                        if(line.payment_method.journal_id){
                            var journal = this.env.pos.journal_by_id[line.payment_method.journal_id[0]]
                            if(journal.is_vale){
                                var folio_de_vale = line.folio_de_vale
                                try {
                                    const vale_api = this.rpc({
                                        model: 'pos.order',
                                        method: 'limpiar_registro_vale',
                                        args: [folio_de_vale],
                                    })
                                    var self = this
                                    vale_api.then(function (res) {
                                        self.currentOrder.is_vale = false
                                        self.currentOrder.state_de_vale = ''
                                        self.currentOrder.folio_de_vale = ''
                                        self.currentOrder.distribuidora_id = ''
                                        self.currentOrder.remove_paymentline(line);
                                        NumberBuffer.reset();
                                        self.render(true);
                                    });
                                } catch(err) {
                                    return this.showPopup('ErrorPopup', {
                                        title: this.env._t('¡ERROR!'),
                                        body: this.env._t('Prueba tu conexion de internet.'),
                                    });
                                }
                            } else{
                                this.currentOrder.remove_paymentline(line);
                                NumberBuffer.reset();
                                this.render(true);
                            }
                        } else{
                            this.currentOrder.remove_paymentline(line);
                            NumberBuffer.reset();
                            this.render(true);
                        }
                    })
                }
                else if (line.get_payment_status() !== 'waitingCancel') {
                    if(line.payment_method.journal_id){
                        var journal = this.env.pos.journal_by_id[line.payment_method.journal_id[0]]
                        if(journal.is_vale){
                            var folio_de_vale = line.folio_de_vale
                            try {
                                const vale_api = this.rpc({
                                    model: 'pos.order',
                                    method: 'limpiar_registro_vale',
                                    args: [folio_de_vale],
                                })
                                var self = this
                                vale_api.then(function (res) {
                                    self.currentOrder.is_vale = false
                                    self.currentOrder.state_de_vale = ''
                                    self.currentOrder.folio_de_vale = ''
                                    self.currentOrder.distribuidora_id = ''
                                    self.currentOrder.remove_paymentline(line);
                                    NumberBuffer.reset();
                                    self.render(true);
                                });
                            } catch(err) {
                                return this.showPopup('ErrorPopup', {
                                    title: this.env._t('¡ERROR!'),
                                    body: this.env._t('Prueba tu conexion de internet.'),
                                });
                            }
                        } else{
                            this.currentOrder.remove_paymentline(line);
                            NumberBuffer.reset();
                            this.render(true);
                        }
                    } else{
                        this.currentOrder.remove_paymentline(line);
                        NumberBuffer.reset();
                        this.render(true);
                    }
                }
            }
        };
    Registries.Component.extend(PaymentScreen, PosPaymentScreen);
    return PaymentScreen;
});
