resource "aws_glue_catalog_database" "lympha" {
  name = "lympha_dev"
}

resource "aws_glue_catalog_table" "raw" {
  name          = "raw_measurements"
  database_name = aws_glue_catalog_database.lympha.name
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${var.datalake_bucket}/${var.raw_prefix}"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "OpenCSVSerde"
      serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"
      parameters = {
        "separatorChar" = ","
        "quoteChar"     = "\""
      }
    }

    columns {
      name = "site_id"
      type = "string"
    }

    columns {
      name = "obs_date"
      type = "string"
    }

    columns {
      name = "do"
      type = "double"
    }

    columns {
      name = "tss"
      type = "double"
    }

    columns {
      name = "temp"
      type = "double"
    }

    columns {
      name = "nh4n"
      type = "double"
    }

    columns {
      name = "no3n"
      type = "double"
    }

    columns {
      name = "tn"
      type = "double"
    }

    columns {
      name = "tp"
      type = "double"
    }

    columns {
      name = "ph"
      type = "double"
    }
  }
}

resource "aws_glue_catalog_table" "predictions" {
  name          = "predicted_ph"
  database_name = aws_glue_catalog_database.lympha.name
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${var.datalake_bucket}/${var.predictions_prefix}"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"

      parameters = {
        "separatorChar" = ","
        "quoteChar"     = "\""
      }
    }

    columns {
      name = "date"
      type = "string"
    }
    columns {
      name = "ph_pred"
      type = "double"
    }
    columns {
      name = "site_id"
      type = "string"
    }
    columns {
      name = "horizon"
      type = "int"
    }
  }
}
