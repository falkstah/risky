// assets/module_folder/libs.js

export function log(msg) {
    console.log('[libs]', msg);
}

// Erlaubt optional die Übergabe der Nachkommastellen (Standard bleibt 2)
export function formatPrice(price, decimals = 2) {
    const num = parseFloat(price);
    if (isNaN(num)) return '0.00';
    return num.toFixed(decimals);
}