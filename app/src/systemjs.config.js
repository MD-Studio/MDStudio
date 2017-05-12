(function (global) {

    // map tells the System loader where to look for things
    var map = {
        '@angular/core': 'npm:@angular/core/bundles/core.umd.js',
        '@angular/common': 'npm:@angular/common/bundles/common.umd.js',
        '@angular/compiler': 'npm:@angular/compiler/bundles/compiler.umd.js',
        '@angular/platform-browser': 'npm:@angular/platform-browser/bundles/platform-browser.umd.js',
        '@angular/platform-browser-dynamic': 'npm:@angular/platform-browser-dynamic/bundles/platform-browser-dynamic.umd.js',
        '@angular/platform-browser/animations': 'npm:@angular/platform-browser/bundles/platform-browser-animations.umd.js',
        '@angular/animations': 'npm:@angular/animations/bundles/animations.umd.js',
        '@angular/animations/browser': 'npm:@angular/animations/bundles/animations-browser.umd.js',
        '@angular/http': 'npm:@angular/http/bundles/http.umd.js',
        '@angular/router': 'npm:@angular/router/bundles/router.umd.js',
        '@angular/forms': 'npm:@angular/forms/bundles/forms.umd.js',

        'rxjs': 'npm:rxjs',
        'angular-in-memory-web-api': 'npm:angular-in-memory-web-api/bundles/in-memory-web-api.umd.js',
        'ngx-cookie': 'npm:ngx-cookie/bundles/ngx-cookie.umd.js',
        'primeng': 'npm:primeng',

        'autobahn': 'npm:autobahn/index.js',
        'when': 'npm:when/when',
        'cbor': 'npm:cbor/lib/cbor.js',
        'when': 'npm:when/when'
    };

    // packages tells the System loader how to load when no filename and/or no extension
    var packages = {
        'rxjs': {
            defaultExtension: 'js'
        },
        'angular2-cookie': {
            main: 'core.js',
            defaultExtension: 'js'
        },
        'primeng': {
            defaultExtension: 'js'
        },
        'autobahn': {
            defaultExtension: 'js'
        },
        '': {
          defaultExtension: 'js'
        }
    };

    var packageNames = [
        '@angular/animations',
        '@angular/common',
        '@angular/compiler',
        '@angular/core',
        '@angular/forms',
        '@angular/http',
        '@angular/platform-browser',
        '@angular/platform-browser-dynamic',
        '@angular/router',
        '@angular/testing',
        '@angular/upgrade'
    ];

    // add package entries for angular packages in the form '@angular/common': { main: 'index.js', defaultExtension: 'js' }
    packageNames.forEach(function (pkgName) {
        packages[pkgName] = {
            defaultExtension: 'js'
        };
    });

    var config = {
        paths: {
            // paths serve as alias
            'npm:': 'node_modules/'
        },
        map: map,
        packages: packages
    }

    // filterSystemConfig - index.html's chance to modify config before we register it.
    if (global.filterSystemConfig) {
        global.filterSystemConfig(config);
    }

    System.config(config);

})(this);