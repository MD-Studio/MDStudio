import * as gulp from 'gulp';
import * as del from 'del';

var cleanCompiledTypeScript = require('gulp-clean-compiled-typescript');

/**
 * This function cleans files in dist directory.
 */
function clean() {
    return del(['dist/**/*']);
}

function cleanTypescript() {
    return gulp.src('src/**/*.ts')
        .pipe(cleanCompiledTypeScript());
}


///////////////////// Clean Tasks /////////////////////

gulp.task('clean:typescript', cleanTypescript);
gulp.task('clean', ['clean:typescript'], clean);