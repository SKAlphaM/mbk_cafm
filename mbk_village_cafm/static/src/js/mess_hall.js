odoo.define('mess_hall_access.mess_hall', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.MessHallScanner = publicWidget.Widget.extend({
        selector: '#mess_hall_wrapper',

        events: {
            'keydown #mess_card_input': '_onKeydownInput',
            'click #mess_check_btn': '_onCheckButtonClick',
        },

        start: function () {
            this.$input = this.$('#mess_card_input');
            this.$defaultState = this.$('#mess_default_state');
            this.$result = this.$('#mess_result');
            this.$resultMessage = this.$('#mess_result_message');
            this.$successCard = this.$('#mess_success_card');
            this.$failedCard = this.$('#mess_failed_card');
            this.$failedText = this.$('#mess_failed_text');

            this.$tenantImage = this.$('#tenant_image');
            this.$tenantName = this.$('#tenant_name');
            this.$tenantCode = this.$('#tenant_code');
            this.$tenantCompany = this.$('#tenant_company');
            this.$menuItems = this.$('#menu_items');
            this.$tenantCard = this.$('#tenant_card');
            this.$counterData = this.$('#counter_data');

            this.$liveDate = this.$('#mess_live_date');
            this.$liveTime = this.$('#mess_live_time');

            this._focusInput();
            this._startClock();

            var self = this;
            this._focusInterval = setInterval(function () {
                self._focusInput();
            }, 400);

            return this._super.apply(this, arguments);
        },

        destroy: function () {
            if (this._focusInterval) {
                clearInterval(this._focusInterval);
            }
            if (this._resetTimer) {
                clearTimeout(this._resetTimer);
            }
            if (this._clockInterval) {
                clearInterval(this._clockInterval);
            }
            return this._super.apply(this, arguments);
        },

        _focusInput: function () {
            if (this.$input.length) {
                this.$input.focus();
            }
        },

        _startClock: function () {
            var self = this;

            if (!this.$liveDate.length || !this.$liveTime.length) {
                return;
            }

            var updateClock = function () {
                var now = new Date();

                var dateText = now.toLocaleDateString(undefined, {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });

                var timeText = now.toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                self.$liveDate.text(dateText);
                self.$liveTime.text(timeText);
            };

            updateClock();
            this._clockInterval = setInterval(updateClock, 1000);
        },

        _onKeydownInput: function (ev) {
            if (ev.key !== 'Enter') {
                return;
            }
            ev.preventDefault();

            var cardNumber = (this.$input.val() || '').trim();
            if (!cardNumber) {
                return;
            }

            this._scanCard(cardNumber);
        },

        _onCheckButtonClick: function (ev) {
            ev.preventDefault();

            var cardNumber = (this.$input.val() || '').trim();
            if (!cardNumber) {
                return;
            }

            this._scanCard(cardNumber);
        },

        _scanCard: function (cardNumber) {
            var self = this;

            ajax.jsonRpc('/mess-hall/scan', 'call', {
                card_number: cardNumber
            }).then(function (response) {
                self._renderResponse(response || {});
                self.$input.val('');
                self._focusInput();
            }).guardedCatch(function () {
                self._renderResponse({
                    status: 'failed',
                    message: 'Something went wrong. Please try again.',
                    tenant: {}
                });
                self.$input.val('');
                self._focusInput();
            });
        },

        _playSound: function (type) {
            try {
                var AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (!AudioContextClass) {
                    return;
                }

                var ctx = new AudioContextClass();
                var oscillator = ctx.createOscillator();
                var gainNode = ctx.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);

                if (type === 'success') {
                    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
                } else {
                    oscillator.frequency.setValueAtTime(220, ctx.currentTime);
                }

                oscillator.type = 'sine';
                gainNode.gain.setValueAtTime(0.12, ctx.currentTime);

                oscillator.start();

                setTimeout(function () {
                    oscillator.stop();
                    ctx.close();
                }, 180);
            } catch (e) {
                console.log('Sound play failed', e);
            }
        },

        _renderResponse: function (response) {
            var tenant = response.tenant || {};

            this.$defaultState.addClass('d-none');
            this.$result.removeClass('d-none');
            this.$successCard.addClass('d-none');
            this.$failedCard.addClass('d-none');
            this.$el.removeClass('mess-state-success mess-state-failed');

            if (response.status === 'success') {
                this.$el.addClass('mess-state-success');
                this._playSound('success');

                this.$resultMessage
                    .removeClass('failed-msg')
                    .addClass('success-msg')
                    .text(response.message || 'Access Granted');

                if (tenant.image_url) {
                    this.$tenantImage.attr('src', tenant.image_url).show();
                } else {
                    this.$tenantImage.attr('src', '').hide();
                }

                this.$tenantName.text(tenant.name || '');
                this.$tenantCode.text(tenant.code || '');
                this.$tenantCompany.text(tenant.company || '');
                this.$menuItems.text(tenant.menu_items || '');
                this.$tenantCard.text(tenant.card_number || '');
                this.$counterData.text(tenant.counter_data || '');

                this.$successCard.removeClass('d-none');
            } else {
                this.$el.addClass('mess-state-failed');
                this._playSound('failed');

                this.$resultMessage
                    .removeClass('success-msg')
                    .addClass('failed-msg')
                    .text(response.message || 'Access Denied');

                this.$failedText.text(response.message || 'You have no access to the mess hall');
                this.$failedCard.removeClass('d-none');
            }

            this._startResetTimer();
        },

        _startResetTimer: function () {
            var self = this;

            if (this._resetTimer) {
                clearTimeout(this._resetTimer);
            }

            this._resetTimer = setTimeout(function () {
                self.$result.addClass('d-none');
                self.$defaultState.removeClass('d-none');
                self.$input.val('');
                self.$el.removeClass('mess-state-success mess-state-failed');
                self._focusInput();
            }, 7000);
        },
    });

    return publicWidget.registry.MessHallScanner;
});