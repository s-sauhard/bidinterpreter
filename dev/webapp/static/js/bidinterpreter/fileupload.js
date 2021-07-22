

$(function() { 

    // var component = {
    //   template: '#vue-file-agent-template',
    //   delimiters: ['[[', ']]'],
    //   data: function(){
    //     console.log("data method called");
    //     return {
    //       fileRecords: [],
    //       message: 'I am sending you the attachments',
    //       fileRecordsForUpload: []
    //     }
    //   },
    //   methods: {
    //     // filesSelected: function (fileRecordsNewlySelected) {
    //     //   console.log('fileSelected()')
    //     //   var validFileRecords = fileRecordsNewlySelected.filter((fileRecord) => !fileRecord.error);
    //     //   console.log("validFileRecords", validFileRecords)
    //     //   console.log('fileRecordsForUpload', this.fileRecordsForUpload)
    //     //   this.fileRecordsForUpload = this.fileRecordsForUpload.concat(validFileRecords);
    //     // },
    //     uploadFiles: function () {
    //       // Using the default uploader. You may use another uploader instead.
    //       console.log("uploadFiles() running")
    //       this.$refs.vueFileAgent.upload(this.uploadUrl, this.uploadHeaders, this.fileRecordsForUpload);
    //       this.fileRecordsForUpload = [];
    //     },
    //     upload: function() {
    //       console.log("upload() called");
    //       this.progress = 0;
    
    //       this.currentFile = this.selectedFiles.item(0);
    //       UploadService.upload(this.currentFile, event => {
    //           this.progress = Math.round((100 * event.loaded) / event.total);
    //       })
    //         .then(response => {
    //           this.message = response.data.message;
    //           return UploadService.getFiles();
    //         })
    //         .then(files => {
    //           this.fileInfos = files.data;
    //         })
    //         .catch(() => {
    //           this.progress = 0;
    //           this.message = "Could not upload the file!";
    //           this.currentFile = undefined;
    //         });
    
    //       this.selectedFiles = undefined;
    //     },
    //     filesSelected: function (fileRecordsNewlySelected) {
    //       console.log("File selected called..")
    //       var validFileRecords = fileRecordsNewlySelected.filter((fileRecord) => !fileRecord.error);
    //       this.fileRecordsForUpload = this.fileRecordsForUpload.concat(validFileRecords);
    //     },
    //     removeFileRecord: function(fileRecord) {
    //       console.log("removeFileRecord called..", this.$refs)
    //       return this.$refs.vfaDemoRef.removeFileRecord(fileRecord);
    //     },
    //     send: function() {
    //       if(this.message.indexOf('attachment') !== -1 && this.fileRecords.length < 1){
    //         if(!confirm('You have mentioned about attachments in your message. Are you sure to send without attachments?')){
    //           return;
    //         }
    //       }
    //       alert('Message sent!');
    //     }
    //   }
    // }
    
    // component.template = '#vue-file-agent-demo';
    // Vue.component('vue-file-agent-demo', component);

// new Vue({ 
//   components: {'file-upload': component}, 
//   el: '#app'});
// });

  var component = {
    delimiters: ['[[', ']]'],
    data: function(){
      return {
        fileRecords: [],
        message: 'I am sending you the attachments',
        fileRecordsForUpload: []
      }
    },
    methods: {

      // upload: function() {
      //   console.log('default upload method here...')
      // },
      //onUpload: function(response) {
      //  console.log('Default uploadData() method called..', response)
      //},
      removeFileRecord: function(fileRecord){
        console.log('Removing file...')
        return this.$refs.vfaDemoRef.removeFileRecord(fileRecord);
      },
      // send: function(){
      //   if(this.message.indexOf('attachment') !== -1 && this.fileRecords.length < 1){
      //     if(!confirm('You have mentioned about attachments in your message. Are you sure to send without attachments?')){
      //       return;
      //     }
      //   }
      //   alert('Message sent!');
      // },
      // uploadFiles: function() { 
      //   console.log('uploadFiles() called')
      //   // Using the default uploader. You may use another uploader instead.
      //   this.$refs.vueFileAgent.upload(this.uploadUrl, this.uploadHeaders, this.fileRecordsForUpload);
      //   this.fileRecordsForUpload = [];
      // },  
    }
  }

  component.template = '#vue-file-agent';
  Vue.component('vue-file-agent', component);

  new Vue({
    el: '#app'
  });

});