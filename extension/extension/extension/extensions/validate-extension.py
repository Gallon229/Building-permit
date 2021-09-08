
###############################################################################
# The file should be in the /extensions folder of the schemas of CityJSON
#
# And the meta-schema file "extension.schema.json" should be in that folder too
###############################################################################

import os
import sys
import json
import jsonschema
import jsonref


def main():
    if len(sys.argv) != 2:
        print("You need to give the path of the CityJSON_Extension file.\nAbort.")
        sys.exit()

    schemapath = os.path.abspath(sys.argv[1])
    js = json.loads(open(schemapath).read())

    metaschemapath = os.path.dirname(schemapath) + '/extension.schema.json'
    jmeta = json.loads(open(metaschemapath).read())

    #-- 1. validation against the extension schema ("meta")
    try:
        jsonschema.validate(js, jmeta)
    except jsonschema.ValidationError as e:
        print ("ERROR:   ", e.message)
        bye(False)
    except jsonschema.SchemaError as e:
        print ("ERROR:   ", e)
        bye(False)

    folder_schemas = os.path.abspath(os.path.dirname(schemapath))
    # base_uri = os.path.join(folder_schemas, "extensions")
    base_uri = os.path.abspath(folder_schemas)

    #-- 2. extraCityObjects
    if "extraCityObjects" in js:
        for nco in js["extraCityObjects"]:
            jtmp = {}
            jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
            jtmp["type"] = "object"
            jtmp["$ref"] = "file://%s#/extraCityObjects/%s" % (schemapath, nco)
            jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
            try:
                jsonschema.Draft7Validator.check_schema(jsotf)
            except jsonschema.exceptions.SchemaError as e:
                print("ERROR:")
                print(e)
                bye(False)
            except jsonref.JsonRefError as e:
                print("ERROR:")
                print(e)
                bye(False)

    #-- 3. extraRootProperties
    if "extraRootProperties" in js:
        for nrp in js["extraRootProperties"]:
            jtmp = {}
            jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
            jtmp["type"] = "object"
            jtmp["$ref"] = "file://%s#/extraRootProperties/%s" % (schemapath, nrp)
            jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
            try:
                jsonschema.Draft7Validator.check_schema(jsotf)
            except  jsonschema.exceptions.SchemaError as e:
                print("ERROR:")
                print(e)
                bye(False)

    #-- 4. extraAttributes
    if "extraAttributes" in js:
        for thetype in js["extraAttributes"]:
            for ea in js["extraAttributes"][thetype]:
                jtmp = {}
                jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
                jtmp["type"] = "object"
                jtmp["$ref"] = "file://%s#/extraAttributes/%s/%s" % (schemapath, thetype, ea)
                jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
                try:
                    jsonschema.Draft7Validator.check_schema(jsotf)
                except  jsonschema.exceptions.SchemaError as e:
                    print("ERROR:")
                    print(e)
                    bye(False)

    bye(True)


def bye(isValid):
    if isValid == True:
        print("\n--> CityJSON Extension is VALID")
    else:
        print("\n--> CityJSON Extension is INVALID :(")
    sys.exit()


if __name__ == '__main__':
    main()