#!/usr/bin/php
<?php
//
// Скрипт для конвертации SNMP Hex-STRING значений вида "4E 6F 64 65 20 4E 6F 64 65 20 31 33 20 6D 65 73" в строку
// Матвей Маринин 2013
//
    function print_usage() {
        echo "Usage: snmp_hex_string <agentIP> <snmp_oid> \n";
        die(1);
    }


    function hexStr2Ascii($hexStr,$separator = ' '){
      $hexStrArr = explode($separator,$hexStr);
      $asciiOut = "";
      foreach($hexStrArr as $octet){
        $char = hexdec($octet);
        if ($char > 0 ) { $asciiOut .= chr($char); }
      }
      return $asciiOut;
    }

//// main ////
    if ( $argc < 2 ) {
        print_usage();
    }

    //snmp timeout in microsecond
    $timeout = 10000000; 

    $snmpvalue = snmpget("$argv[1]", "public", "$argv[2]", $timeout, 1);
    if ( $snmpvalue ) {
      $split = explode(':', $snmpvalue, 2);
      //$output = "$split[0] $split[1]: ";
      $output = "";

      if (count($split) == 2) {
        if ( strcmp($split[0], 'Hex-STRING') == 0 ) {
          $output .= hexStr2Ascii($split[1]);
        } else {
          $output = $split[1];
        }
      } else {
        $output = $snmpvalue;
      }

      echo "$output\n";
    }

?>
