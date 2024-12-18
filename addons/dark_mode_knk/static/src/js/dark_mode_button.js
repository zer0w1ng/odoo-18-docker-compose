/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { patch } from '@web/core/utils/patch';
import { cookie } from "@web/core/browser/cookie";

class DarkModeSystray extends Component {
    static props = {}

    _applyTheme() {
        if (this.state.color_scheme === 'dark') {
            document.body.classList.add('knk_night_mode');
            // moonButton.style.display = 'none';
            // sunButton.style.display = 'inline-block';

        } else {
            document.body.classList.remove('knk_night_mode');
            // moonButton.style.display = 'inline-block';
            // sunButton.style.display = 'none';
        }
    }
    _onClick() {
        // debugger;
        if(this.state.color_scheme == 'light'){
            this.state.color_scheme = 'dark';
            cookie.set('color_scheme', this.state.color_scheme);
            console.log('LIGHT', this.state.color_scheme);
        }else{
            this.state.color_scheme = 'light';
            cookie.set('color_scheme', this.state.color_scheme);
            console.log('Dark', this.state.color_scheme);
        }
        this._applyTheme();
    }
    setup() {
        this.state = useState({
            color_scheme: 'light'
        });
        super.setup();
        // const storedTheme = this.state.color_scheme;
        const storedTheme = cookie.get('color_scheme');
        if (storedTheme) {
          this.state.color_scheme = storedTheme;
        }
        else{
            cookie.set('color_scheme', this.state.color_scheme);
        }
        this._applyTheme();
        onWillUpdateProps((nextProps) => {
            this._applyTheme();
        });
    }
}
DarkModeSystray.template = "dark_mode_knk.SystrayItem";

export const systrayItem = {
    Component: DarkModeSystray,
    isDisplayed: () => true, 
};

registry.category("systray").add("DarkModeSystrayItem", systrayItem, { sequence: 1 });
