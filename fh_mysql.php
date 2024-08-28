<?
	// Edit database details on the next two lines
	mysql_connect("213.171.200.34", "Kazumi7884", "Database1!");
	mysql_select_db("kazumi7884_main");

	$result = mysql_query("show table status");

	$size = 0;
	$out = "";
	while($row = mysql_fetch_array($result)) {
		$size += $row["Data_length"];
		$size += $row["Index_length"];
		$out .= $row["Name"] .": ". 
		round(($row["Data_length"]/1024)/1024, 2) ."<br>\n";
	}

	$size = round(($size/1024)/1024, 1);

	echo $out ."<br>\n";
	echo "Total MySQL db size: $size";
?>

