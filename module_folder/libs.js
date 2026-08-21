// module_folder/libs.js

export function log(msg) {
    console.log('[libs]', msg);
}

export function formatPrice(price) {
    return parseFloat(price).toFixed(2);
}