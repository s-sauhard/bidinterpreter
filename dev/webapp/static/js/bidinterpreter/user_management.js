function toggle(source) {
    checkboxes = document.querySelectorAll('input[name=action]');
    for(var i in checkboxes)
        checkboxes[i].checked = source.checked;
}

$(function() {
    function getCookie(c_name)
    {
        if (document.cookie.length > 0)
        {
            c_start = document.cookie.indexOf(c_name + "=");
            if (c_start != -1)
            {
                c_start = c_start + c_name.length + 1;
                c_end = document.cookie.indexOf(";", c_start);
                if (c_end == -1) c_end = document.cookie.length;
                return unescape(document.cookie.substring(c_start,c_end));
            }
        }
        return "";
    }

    var update_diaglog = function(action = "remove") {
        let confirm = $('#confirm');

        switch(action) {

            case "remove":
                console.log("remove chosen in case...");
                meta = {
                    title:        "Confirm Delete",
                    message:      "Are you sure you want to remove these users from your deal?",
                    button_class: "btn btn-danger",
                    button_icon:  "fa fa-trash-alt",
                    button_text:  " Remove User"
                }
                break;

            case "update_view":
            case "update_bid":
                meta = {
                    title:        "Confirm Permission",
                    message:      "Are you sure you want to change this users permission?",
                    button_class: "btn btn-primary",
                    button_icon:  "fas fa-shield-alt",
                    button_text:  " Update User"
                }
                break;

            default:
                console.log("default meta set.")
                meta = {
                    title:        "Select a user",
                    message:      "Pleas select users to apply actions to first!",
                    button_class: "btn btn-primary",
                    button_icon:  "fas fa-users-alt",
                    button_text:  " Select Users First"
                }
        }

        // If user doesn't select any users.
        let checked = document.querySelectorAll('input[name=action]:checked');
        if (!checked.length) {
            console.log("Users not selected!")
            meta = {
                title:        "Select a User",
                message:      "Pleas select users to apply actions to first!",
                button_class: "btn btn-danger",
                button_icon:  "fa fa-lock",
                button_text:  " Select Users First"
            }
            $("#delete").prop('disabled', true);
        } else {
            $("#delete").prop('disabled', false);
        }

        console.log("using meta:", meta, "action:", action);

        confirm.find("h5").text(meta.title);
        confirm.find(".modal-body p").text(meta.message);
        confirm.find("#remove-user-icon")[0].className = meta.button_icon;
        confirm.find("#delete")[0].className = meta.button_class;
        confirm.find("#confirm-button").text(meta.button_text);
    }



    document.getElementById('close-button').addEventListener('click', () => {
        location.reload();
    })

    document.getElementById('invite-button').addEventListener('click', ()=>{

        let url = ""
        let csrfmiddlewaretoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value
        let username  = document.getElementById('username').value
        let email     = document.getElementById('email').value
        let user_type = document.getElementById('user_type').value

        let request_data = { 
            user_type:           user_type, 
            csrfmiddlewaretoken: csrfmiddlewaretoken
        }

        // Set username or email but not both.  Might be worth setting a new parameter for the backend.
        if (email) {
            request_data['email']    = email
            request_data['action']   = "external_invite"
        } else if (username) {
            request_data['username'] = username
            request_data['action']   = "add_user"
        }
        var message             = document.getElementById('invite-message')
        var status              = document.getElementById('status')
        var invite_button       = document.getElementById('invite-button')
        invite_button.disabled  = true
        status.className        = 'fas fa-sync fa-spin'
        // message.innerHTML = '<i class=""></i>Please wait!'

        fetch(url, { 
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                "X-CSRFToken": getCookie("csrftoken")
            },
            method:  "POST",
            body:    JSON.stringify(request_data)
        })
            .then(res => res.json()) // parse response as JSON (can be res.text() for plain response)
            .then(response => {
                // here you do what you want with response
                console.log("Response is:", response)
                
                message.innerHTML = response['message']
                status.className  = 'fa fa-door-open'
                invite_button.disabled = false

                if(!response['error']) {
                    message.classList.remove('text-danger')
                } else {
                    message.classList.add('text-danger')
                }
            })
            .catch(err => {
                status.className  = 'fa fa-door-open'
                invite_button.disabled = false
                message.innerHTM = "There was an error with your request."
                console.log("there was an error", err)
                alert("sorry, there are no results for your search")
            });
    });

    // change diaglog text if set
    console.log("setting action button click")
    document.getElementById('action-button').addEventListener('click', () =>  {
        console.log("UPdating dialog:", document.getElementById('action').value)
        update_diaglog(
            action = document.getElementById('action').value
        );
        // $('#confirm').modal()
    })
    // document.getElementById('action-button').off('click').addEventListener('click', () => {

    // })
    

    // Remove user 
    document.getElementById('delete').addEventListener('click', ()=> {
        let checked = document.querySelectorAll('input[name=action]:checked');
        if (checked.length) {
            let csrfmiddlewaretoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value
            let users               = Array.from(checked).map((item) => ~~item.value);
            let url                 = ""
            let action              = document.getElementById('action').value
            let delete_icon         = document.getElementById('remove-user-icon')
            delete_icon.className  = "fas fa-spinner fa-pulse"

            fetch(url, { 
                headers: { 
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                method:  "POST",
                body:    JSON.stringify({ users: users, csrfmiddlewaretoken: csrfmiddlewaretoken, action: action})
            })
                .then(res => res.json())
                .then(response => {
                    // here you do what you want with response
                    console.log("Response is:", response)
                    location.reload();
                });
        }
        console.log(checked, checked.length)
    });

    $('.delete_bid').on('click', function(e) {
        var link = $(this).closest('a');
        e.preventDefault();
        $('#confirm').modal({
            backdrop: 'static',
            keyboard: false
        })
        .on('click', '#delete', function(e) {
            window.location = link.attr('href')
        });
        $("#cancel").on('click',function(e){
            e.preventDefault();
            $('#confirm').modal.model('hide');
        });
    });
});