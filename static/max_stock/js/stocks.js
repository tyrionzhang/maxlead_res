$(document).ready(function(){
	var elem_name = $('#main').attr('data-name');
	$('#'+elem_name).addClass('checked');

	$('.ul-name-list li').on('click', function() {
		$('.ul-name-list .checked').removeClass('checked');
		$(this).addClass('checked');
	});
	$('.ul-menu li').on('click', function() {
		$('.ul-menu .checked').removeClass('checked');
		$(this).addClass('checked');
	});

	var rel_height = $(window).height();
	$('.wrap-paper').style = 'height:' + rel_height+'px';

	$("#form_threshold").submit(function(e){
		e.preventDefault();
	  });

	$('#btn-threshold').on('click',function () {
		var id = $('input[name="id"]').val();
		if(!id){
			$(this).attr("disabled", true);
		}

		var data = {
		  'sku':$('input[name="sku"]').val(),
		  'warehouse':$('select[name="sel_warehouse"]').val(),
		  'threshold':$('input[name="threshold"]').val(),
		  'id':id
		};
		$.post('/admin/max_stock/threshold_add/',data,function (re) {
		   if(re.code==1){
			   window.location.reload();
		   }
		   if(re.code==0){
			   alert(re.msg);
		   }
		   if(re.code==66){
			   window.location.href='/admin/max_stock/login/';
		   }
		},'json');
		return false;
	});

	$('.threshold-edit').on('click', function () {
		var elem = $('#form_threshold');
		$('.wrap-paper').removeClass('hide');
		$('.save-threshold').removeClass('hide');
		$("#btn-threshold").removeAttr("disabled");
		elem[0].reset();
		var id = $(this).data('id');
		var id_el = '<input type="hidden" name="id" value="'+id+'">';
		$.post('/admin/max_stock/get_threshold/',{'id':id},function (re) {
		   if(re.code==1){
			   elem.append(id_el);
			   $('input[name="sku"]').val(re.data.sku);
			   $('select[name="sel_warehouse"]').val(re.data.warehouse);
			   $('input[name="threshold"]').val(re.data.threshold);
		   }
		   if(re.code==0){
			   alert(re.msg);
		   }
		   if(re.code==66){
			   window.location.href='/admin/max_stock/login/';
		   }
		},'json');
		return false;
    });

	$('#threshold_add').on('click', function(){
		$('.wrap-paper').removeClass('hide');
		$('.save-threshold').removeClass('hide');
		$("#btn-threshold").removeAttr("disabled");
		$('#form_threshold')[0].reset();
	});
	$('.wrap-paper').on('click', function(){
		$('.wrap-paper').addClass('hide');
		$('.save-threshold').addClass('hide');
	});
	$('body').on('click', '.btn-close', function(){
		$('.wrap-paper').addClass('hide');
		$('.save-block-info').addClass('hide');
	});
	$('.tr-stock-blue1').attr('style','background-color: #db5461;');
});