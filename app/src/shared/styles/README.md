###Folder styles

This folder contains all global CSS styles for the LIEStudio app as Sass .scss
files.

The main.scss file will serve as the final Sass compiled .css endpoint file 
containing all global app style definitions in one file.

Individual Angular 2 components main implement their own styles or global style
overwrites that operate in the scope of the component. These styles are defined
in .scss files in the component directory.

Sass style variables that determine the look and feel of the app theme are 
conveniatly gathered in the theme_variables.scss file. All substyle defenitions
inherit from this variables file.