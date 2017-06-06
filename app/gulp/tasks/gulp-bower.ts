import * as bower from 'gulp-bower';
import * as gulp from 'gulp';


gulp.task('bower:dist', function() {
   return bower();
});