document.addEventListener('DOMContentLoaded', async () => {
    const { initModules } = await import('/module_folder/modules.js');
    const { libs, socket } = await initModules();

    libs.log('Module geladen');
    socket.on('ping', data => console.log('PING:', data));
});
