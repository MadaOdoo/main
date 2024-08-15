odoo.define('xma_pos_voucher_redemption.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { _t } = require('web.core');

    const PosPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {
            async addNewPaymentLine({ detail: paymentMethod }) {
                let transaction_id = false;
                if (paymentMethod.is_bank_terminal){
                    let transaction_response = await this.showPopup('TransactionPopUp')
                    if (transaction_response.confirmed){
                        transaction_id = transaction_response.payload;
                    } else {
                        return false
                    }
                }
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
                    if (!this.currentOrder.get_partner()) {
                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                            title: this.env._t('Por favor, seleccione el cliente'),
                            body: this.env._t(
                                'Debe seleccionar el cliente antes de poder enviar una orden con vale.'
                            ),
                        });
                        if (confirmed) {
                            this.selectPartner();
                        }
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
                        startingValue: 'A-00004-0001',
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
                                    var monto_a_pagar = this.currentOrder.get_due() > 0 ? this.currentOrder.get_due() : 0
                                    var obj = {};
                                    let monto_total = 0;
                                    let monto_as_text = '';
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
                                                        const res_opciones_pago = await this.rpc({
                                                            model: 'pos.order',
                                                            method: 'get_opciones_de_pago',
                                                            args: [vale_api.distribuidoraId,monto_sin_symbol],
                                                        });
                                                        monto_total = res_opciones_pago.monto_total;
                                                        monto_as_text = res_opciones_pago.monto_as_text;
                                                        if(res_opciones_pago.status_code == 200){
                                                            const fin_lista = [];
                                                            const ids = [];
                                                            const lista = res_opciones_pago.lista;
                                                            for (let i = 0; i < lista.length; i++) {
                                                                fin_lista.push({id:lista[i].configId, name:lista[i].opcion});
                                                                ids[lista[i].configId] = lista[i];
                                                            }
                                                            const selectionList = [{
                                                                id: null,
                                                                label: '---Seleccione el plazo de pago---',
                                                                isSelected: null,
                                                                item: {id:null, name:''},
                                                            }];
                                                            const subs = fin_lista.map(opciones_pago => ({
                                                                id: opciones_pago.id,
                                                                label: opciones_pago.name,
                                                                isSelected: null,
                                                                item: opciones_pago,
                                                            }));
                                                            const lista_pagos = selectionList.concat(subs);
                                                            const { confirmed, payload: selectedOptionPago } = await this.showPopup('SelectionPopup', {
                                                                title: this.env._t('Opciones de Plazo'),
                                                                list: lista_pagos,
                                                            });
                                                            if (confirmed) {
                                                                if(selectedOptionPago.id != null){
                                                                    obj = ids[selectedOptionPago.id];
                                                                } else {
                                                                    return false;
                                                                }
                                                            } else {
                                                                return false;
                                                            }
                                                        } else if (res_opciones_pago.status_code == 400){
                                                            await this.showPopup('ErrorPopup', {
                                                                title: this.env._t('¡Error '+res_opciones_pago.status_code+'!'),
                                                                body: this.env._t(res_opciones_pago.message+'.'),
                                                            });
                                                            return false;
                                                        } else {
                                                            return false;
                                                        }
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
                                    } else {
                                        var _monto_a_pagar = this.env.pos.format_currency(monto_a_pagar);
                                        await this.showPopup('ModalDialogWarningPopup', {
                                            title: this.env._t('¡ADVERTENCIA!'),
                                            body1: this.env._t('La distribuidora no cuenta con saldo disponible suficiente para procesar la venta'),
                                        })
                                        return false;
                                    }
                                    await this.showPopup('ModalDialogSuccess', {
                                        title: this.env._t('¡'+vale_api.nombreDistribuidora+'!'),
                                        body1: this.env._t('El vale con el folio'),
                                        text1: this.env._t(vale_api.folio),
                                        body2: this.env._t(', se utilizo un saldo de'),
                                        text2: this.env._t(monto_con_symbol),
                                        body3: this.env._t('y se encuentra en estado'),
                                        text3: this.env._t(vale_api.estatus),
                                        imageUrl: this.env._t(vale_api.firma),
                                    })
                                    let result = this.currentOrder.add_paymentline(paymentMethod)
                                    if(result){
                                        if(transaction_id){
                                            result.transaction_id = transaction_id;
                                        }
                                        result.folio_de_vale = vale_api.folio;
                                        this.currentOrder.folio_de_vale = vale_api.folio;
                                        this.currentOrder.is_vale = true;
                                        this.currentOrder.state_de_vale = 'Canjeado';
                                        this.currentOrder.distribuidora_id = vale_api.distribuidoraId;
                                        this.currentOrder.nombre_distribuidora = vale_api.nombreDistribuidora;
                                        this.currentOrder.cantidad_pagos = obj.cantidadPagos || -1;
                                        this.currentOrder.monto_seguro = obj.montoSeguro;
                                        this.currentOrder.pago_quincenal = obj.pagoQuincenal;
                                        this.currentOrder.total = obj.total;
                                        this.currentOrder.fecha = obj.fecha;
                                        this.currentOrder.config_id = obj.configId;
                                        this.currentOrder.nombre_cliente = vale_api.nombre_cliente;
                                        this.currentOrder.cliente_telefono = vale_api.cliente_telefono;
                                        this.currentOrder.ife = vale_api.ife;
                                        this.currentOrder.monto_total = monto_total;
                                        this.currentOrder.monto_as_text = monto_as_text;
                                        this.currentOrder.ciudad = vale_api.ciudad;
                                        result.set_amount(monto_a_pagar);
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
                    this.env.pos.get_order().selected_paymentline.transaction_id = transaction_id;
                }
            }
            deletePaymentLine(event) {
                var self = this;
                const { cid } = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);

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
                                        self.currentOrder.nombre_distribuidora = ''
                                        self.currentOrder.cantidad_pagos = 0;
                                        self.currentOrder.monto_seguro = 0;
                                        self.currentOrder.pago_quincenal = 0;
                                        self.currentOrder.total = 0;
                                        self.currentOrder.fecha = '';
                                        self.currentOrder.config_id = 0;
                                        self.currentOrder.nombre_cliente = '';
                                        self.currentOrder.cliente_telefono = '';
                                        self.currentOrder.ife = '';
                                        self.currentOrder.monto_total = 0;
                                        self.currentOrder.monto_as_text = '';
                                        self.ciudad = '';
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
                                    self.currentOrder.nombre_distribuidora = ''
                                    self.currentOrder.cantidad_pagos = 0;
                                    self.currentOrder.monto_seguro = 0;
                                    self.currentOrder.pago_quincenal = 0;
                                    self.currentOrder.total = 0;
                                    self.currentOrder.fecha = '';
                                    self.currentOrder.config_id = 0;
                                    self.currentOrder.nombre_cliente = '';
                                    self.currentOrder.cliente_telefono = '';
                                    self.currentOrder.ife = '';
                                    self.currentOrder.monto_total = 0;
                                    self.currentOrder.monto_as_text = '';
                                    self.ciudad = '';
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
            async _finalizeValidation() {
                if(this.currentOrder.is_vale){
                    if(this.currentOrder.get_partner()) {
                        try {
                            var datos = {
                                "montoCredito": this.currentOrder.cantidad_pagos * this.currentOrder.pago_quincenal,
                                "configId": this.currentOrder.config_id,
                                "folio": this.currentOrder.folio_de_vale,
                                "afiliado":"MADA",
                                "usuarioId": '',
                                "cliente":{
                                    "nombres":"",
                                    "primerApellido":"",
                                    "segundoApellido":"",
                                    "curp":"",
                                    "celular":"" 
                                },
                                // "pagare":"00033"
                            }
                            let result = await this.rpc({
                                model: 'pos.order',
                                method: 'validar_canje_credito',
                                args: [datos,this.env.pos.config.token],
                            });
                            if(result.status_code == 200){
                                const fechasPago = result.fechasPago;
                                if(fechasPago.length > 0){
                                    var str_fechas = '';
                                    for (let i = 0; i < fechasPago.length; i++) {
                                        str_fechas += fechasPago[i] + ',';
                                    }
                                    if(str_fechas != '') {
                                        str_fechas = str_fechas.substring(0, str_fechas.length - 1);
                                        this.currentOrder.str_fechas = str_fechas
                                        this.currentOrder.porcentaje_comision = result.porcentaje_comision
                                        this.currentOrder.monto_seguro_por_quincena = result.monto_seguro_por_quincena
                                        await this.rpc({
                                            model: 'pos.order',
                                            method: 'save_model_cajeo_vales',
                                            args: [this.currentOrder.distribuidora_id,this.currentOrder.folio_de_vale],
                                        })
                                    } else {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('¡ERROR!'),
                                            body: this.env._t('Algo salio mal vuelva a intentarlo.'),
                                        });
                                        return false;
                                    }
                                } else {
                                    await this.showPopup('ErrorPopup', {
                                        title: this.env._t('¡ERROR!'),
                                        body: this.env._t('Algo salio mal vuelva a intentarlo.'),
                                    });
                                    return false;
                                }
                            } else if (result.status_code == 404){
                                await this.showPopup('ModalDialogWarningPopup', {
                                    title: this.env._t('¡ADVERTENCIA!'),
                                    body1: this.env._t(result.message+'.'),
                                })
                                return false;
                            }
                        } catch (_e) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('¡ERROR!'),
                                body: this.env._t('Prueba tu conexion de internet.'),
                            });
                            return false;
                        }
                    } else {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Es necesario seleccionar un cliente'),
                        });
                        return false;
                    }
                }
                await super._finalizeValidation(...arguments);
            }
        };
    Registries.Component.extend(PaymentScreen, PosPaymentScreen);
    return PaymentScreen;
});
