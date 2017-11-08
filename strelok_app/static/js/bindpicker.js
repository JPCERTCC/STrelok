function bindPicker(){
    dtpOption = {format:'Y-m-d H:i',defaultTime:'00:00'};
    $('input#id_published').datetimepicker(dtpOption);
    $('input#id_first_seen').datetimepicker(dtpOption);
    $('input#id_last_seen').datetimepicker(dtpOption);
    $('input#id_valid_from').datetimepicker(dtpOption);
    $('input#id_valid_until').datetimepicker(dtpOption);
    $('input#id_first_observed').datetimepicker(dtpOption);
    $('input#id_last_observed').datetimepicker(dtpOption);
}
