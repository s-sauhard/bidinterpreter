# bidinterpreter

## Project Organization
```
├── media                   <- File uploads and static files
├── project                 <- All code related to Python and HTML
│   ├── apps                <- Python Django applications
|   |   ├── bidinterpreter
|   |   └── profile 
│   └── templates           <- Top-level HTML templates for applications
|   |   ├── global          <- Site-wide templates that control the overall look and feel of the app (ie: base.html)
|   |   ├── bidinterpreter  <-- bidinterpreter app related HTML templates
|   └── └── profile         <-- Custom user profile behavior and forms
├── README.md               <- The top-level README for developers using this project.
├── settings.py
├── manage.py
└── ...etc
```

The reasoning for this change is mainly for better organization but also the separation of templates as we customize the app more.  Previsouly, to create a profile form for the "profile" app, would mean putting the Python code in the `profile` app directory, and then the HTML for the form in the `bidinterpret/templates` directory.  Now templates is independent of _applications_ but so are the different application templates.  This also simplifies how we `extend` global assets such as `base.html` and possibly design other areas of the site at scale.  

Starting Locally
`sudo docker-compose -f docker-compose-local.yml up`

> TLDR; The app is more organized so it's easier to work with as we add more files and code. 
