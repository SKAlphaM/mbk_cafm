/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, onWillUpdateProps, useState, xml } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class TicketTimerField extends Component {
    static template = xml`<span t-esc="state.displayValue"/>`;
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            displayValue: "",
        });
        this.timer = null;

        onMounted(() => {
            this._refreshFromRecord(this.props);
        });

        onWillUpdateProps((nextProps) => {
            this._refreshFromRecord(nextProps);
        });

        onWillUnmount(() => {
            this._clearTimer();
        });
    }

    _clearTimer() {
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    }

    _parseServerDatetime(value) {
        if (!value) {
            return null;
        }
        if (value instanceof Date) {
            return value;
        }
        if (typeof value === "string") {
            const normalized = value.replace(" ", "T");
            const parsed = new Date(normalized);
            if (!isNaN(parsed.getTime())) {
                return parsed;
            }
        }
        return null;
    }

    _getDurationMs(startDate, endDate) {
        if (!startDate || !endDate) {
            return 0;
        }
        return Math.max(endDate.getTime() - startDate.getTime(), 0);
    }

    _formatDuration(durationMs) {
        const totalSeconds = Math.floor(durationMs / 1000);
        const days = Math.floor(totalSeconds / 86400);
        const remainingAfterDays = totalSeconds % 86400;
        const hours = Math.floor(remainingAfterDays / 3600);
        const minutes = Math.floor((remainingAfterDays % 3600) / 60);
        const seconds = remainingAfterDays % 60;

        const hh = String(hours).padStart(2, "0");
        const mm = String(minutes).padStart(2, "0");
        const ss = String(seconds).padStart(2, "0");

        return `${days ? `${days} days ` : ""}${hh}:${mm}:${ss}`;
    }

    _refreshFromRecord(props) {
        this._clearTimer();

        const data = props.record?.data || {};
        const startTime = this._parseServerDatetime(data.start_time);
        const endTime = this._parseServerDatetime(data.end_time);
        const isInProgress = !!data.is_in_progress;

        let durationMs = 0;
        if (startTime) {
            durationMs = this._getDurationMs(startTime, endTime || new Date());
        }

        this.state.displayValue = this._formatDuration(durationMs);

        if (startTime && isInProgress && !endTime) {
            this._startTicker(startTime);
        }
    }

    _startTicker(startTime) {
        const tick = () => {
            const now = new Date();
            const durationMs = this._getDurationMs(startTime, now);
            this.state.displayValue = this._formatDuration(durationMs);
            this.timer = setTimeout(tick, 1000);
        };
        this.timer = setTimeout(tick, 1000);
    }
}

export const ticketTimerField = {
    component: TicketTimerField,
    supportedTypes: ["float"],
};

registry.category("fields").add("ticket_timer", ticketTimerField);