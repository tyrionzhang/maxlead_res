function getWeekOfYear(){
    var today = new Date();
    var firstDay = new Date(today.getFullYear(),0, 1);
    var dayOfWeek = firstDay.getDay();
    var spendDay= 1;
    if (dayOfWeek !=0) {
        spendDay=7-dayOfWeek+1;
    }
    firstDay = new Date(today.getFullYear(),0, 1+spendDay);
    var d =Math.ceil((today.valueOf()- firstDay.valueOf())/ 86400000);
    var result =Math.ceil(d/7);
    return result+1;
}

$(document).ready(function(){
    $('body').on('click', '.select-li', function () {
        var brand = $(this).html();
        var ul = $(this).parents('.ul-select');
        ul.prev('input').val(brand);
        ul.hide();
        return false;
    });
    $('.input-sel').click(function () {
        $(this).next().show();
    });

    $('.range-type').click(function () {
        var date = new Date();  //创建对象
        var y = date.getFullYear();
        var range_type = $(this).val();
        if(range_type == 'Monthly'){
            var max_month = date.getMonth()+1;
            if (max_month < 10){
                max_month= '0' + max_month;
            }
            $('input[name="week"]').attr('style', 'display:none');
            $('input[name="month"]').removeAttr('style');
            $('input[name="month"]').attr('max', y+'-'+ max_month);
            $('input[name="month"]').attr('min', y+'-01');
        }else {
            var weeks = getWeekOfYear() - 1;
            $('input[name="month"]').attr('style', 'display:none');
            $('input[name="week"]').removeAttr('style');
            $('input[name="week"]').attr('max', y+'-W'+ weeks);
            $('input[name="week"]').attr('min', y+'-W01');
        }
    });

    $('body').click(function (e) {
        if (!$(e.target).attr('class') || $(e.target).attr('class').indexOf('input-sel') == -1)
        $('.ul-select').hide();
    });
});

function comparer(index) {
  return function(a, b) {
    var valA = getCellValue(a, index),
      valB = getCellValue(b, index);
    return $.isNumeric(valA) && $.isNumeric(valB) ?
      valA - valB : valA.localeCompare(valB);
  };
}

function getCellValue(row, index) {
  return $(row).children('td').eq(index).text();
}
