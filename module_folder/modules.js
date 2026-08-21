// module_folder/modules.js

import * as Libs from './libs.js';
import { initSocket } from './socket.js';

export async function initModules() {
    console.log('[modules] Initialisiere Module…');

    const libs = Libs;
    const socket = await initSocket();

    console.log('[modules] Module bereit.');
    return { libs, socket };
}

export { Libs, initSocket };
