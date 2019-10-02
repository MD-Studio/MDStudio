(function (global) {

    // map tells the System loader where to look for things
    var map = {
        "@angular/core": "npm:@angular/core/bundles/core.umd.js",
        "@angular/common": "npm:@angular/common/bundles/common.umd.js",
        "@angular/compiler": "npm:@angular/compiler/bundles/compiler.umd.js",
        "@angular/platform-browser": "npm:@angular/platform-browser/bundles/platform-browser.umd.js",
        "@angular/platform-browser-dynamic": "npm:@angular/platform-browser-dynamic/bundles/platform-browser-dynamic.umd.js",
        "@angular/platform-browser/animations": "npm:@angular/platform-browser/bundles/platform-browser-animations.umd.js",
        "@angular/animations": "npm:@angular/animations/bundles/animations.umd.js",
        "@angular/animations/browser": "npm:@angular/animations/bundles/animations-browser.umd.js",
        "@angular/http": "npm:@angular/http/bundles/http.umd.js",
        "@angular/router": "npm:@angular/router/bundles/router.umd.js",
        "@angular/forms": "npm:@angular/forms/bundles/forms.umd.js",

        "rxjs": "npm:rxjs",
        "angular-in-memory-web-api": "npm:angular-in-memory-web-api/bundles/in-memory-web-api.umd.js",
        "ngx-cookie": "npm:ngx-cookie/bundles/ngx-cookie.umd.js",
        "primeng": "npm:primeng"
    };

    // packages tells the System loader how to load when no filename and/or no extension
    var packages = {
        "": { defaultExtension: "js" },
        "rxjs": { defaultExtension: "js" },
        "angular2-cookie": { main: "core.js", defaultExtension: "js" },
        "primeng": { defaultExtension: "js" },
        "@angular/animations": { defaultExtension: "js" },
        "@angular/common": { defaultExtension: "js" },
        "@angular/compiler": { defaultExtension: "js" },
        "@angular/core": { defaultExtension: "js" },
        "@angular/forms": { defaultExtension: "js" },
        "@angular/http": { defaultExtension: "js" },
        "@angular/platform-browser": { defaultExtension: "js" },
        "@angular/platform-browser-dynamic": { defaultExtension: "js" },
        "@angular/router": { defaultExtension: "js" },
        "@angular/testing": { defaultExtension: "js" },
        "@angular/upgrade": { defaultExtension: "js" }
    };

    var config = {
        paths: {
            // paths serve as alias
            "npm:": "node_modules/"
        },
        map,
        packages
    };

    // filterSystemConfig - index.html's chance to modify config before we register it.
    if (global.filterSystemConfig) {
        global.filterSystemConfig(config);
    }

    System.config(config);

}(this));