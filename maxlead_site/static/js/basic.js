$(document).ready(function(){

    $("#menuSwitch").click(function(){
      $("#userNav > ul").toggle();
    }); //header nav menu
    
    $("#ifmp,#prrCancel").click(function(){
      $("#pwdReset").toggle();
    }); //sign in reset pwd

    $("#addNewMiner, #nmtCancel").click(function(){
      $("#addMinerTask").toggle();
      $("#task_add").removeAttr('disabled');
    }); //add new Miner task
    
    $("#selectAllUser").click(function(){
      if(this.checked){
      $(".userAdmin > table [type='checkbox']").attr("checked", true);} else {
      $(".userAdmin > table [type='checkbox']").attr("checked", false);}   
      });
    //select all users
    //dashboard click 
    

    $("input[name=selectallListing]").click(function(){
      if(this.checked){
      $(".listMgm > table [type='checkbox']").attr("checked", true);} else {
      $(".listMgm > table [type='checkbox']").attr("checked", false);}   
      });
    //select all listing

    $("#addASINButton, #editASINCancel").click(function(){
      $("#editASIN").toggle();
    }); //add edit ASIN    

    $(".screenshotButton, #screenshot").click(function(){
      $("#screenshot").toggle();
    }); //screenshot pop up  

    $(".asinON, .asinOFF").click(function(){
        if ($(this).attr("class") == "asinON"){
            $(this).attr("class","asinOFF");}
        else {
            $(this).attr("class","asinON");
        }
          
    }); //asin status 

    $(".rvON, .rvOFF").click(function(){
        if ($(this).attr("class") == "rvON"){
            $(this).attr("class","rvOFF");}
        else {
            $(this).attr("class","rvON");
        }
          
    }); //review status
    
    $(".listON, .listOFF").click(function(){
        if ($(this).attr("class") == "listON"){
            $(this).attr("class","listOFF");}
        else {
            $(this).attr("class","listON");
        }
          
    }); //review status
    
    $(".actIn > button, #actOut, .actIn").click(function(){
        $("#actOut").toggle();
    }); //act details

    
});