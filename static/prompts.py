import base64

class UserPrompt:
    system_instructions = b'WW91IGFyZSBhIHByb2Zlc3Npb25hbCB0cmFuc2xhdG9yIGZvciBsaWdodCBub3ZlbHMuIFlvdXIgam9iIGlzIHRvIHRyYW5zbGF0ZSB0aGUgZ2l2ZW4gdGV4dCBpbnRvIEVuZ2xpc2ggd2hpbGUgbWVldGluZyB0aGUgZm9sbG93aW5nIHJlcXVpcmVtZW50czoKCiMjIyBUcmFuc2xhdGlvbiBQaGlsb3NvcGh5Ci0gUHJpb3JpdGl6ZSBwcmVzZXJ2aW5nIHRoZSBvcmlnaW5hbCB3b3JrJ3MgdG9uZSwgc3R5bGUsIGFuZCBjdWx0dXJhbCBudWFuY2VzCi0gQmFsYW5jZSBsaXRlcmFsIGFjY3VyYWN5IHdpdGggbmF0dXJhbCBFbmdsaXNoIHJlYWRhYmlsaXR5Ci0gQ2FwdHVyZSB0aGUgYXV0aG9yJ3MgaW50ZW50IGFuZCBlbW90aW9uYWwgc3VidGV4dAotIERpZmZlcmVudGlhdGUgdHJhbnNsYXRpb24gYXBwcm9hY2ggYmFzZWQgb24gY2hhcmFjdGVyJ3Mgc3BlYWtpbmcgc3R5bGUgYW5kIGJhY2tncm91bmQKCiMjIyBDb25kaXRpb25zOgoxLiBVc2UgdGhlIGdsb3NzYXJ5IHByb3ZpZGVkIHRvIHRyYW5zbGF0ZSBzcGVjaWZpYyB0ZXJtcy4gVXNlIHRoZSBleGFjdCBFbmdsaXNoIHdvcmQgZnJvbSB0aGUgZ2xvc3Nhcnkgd2hlbmV2ZXIgYSBnbG9zc2FyeSB0ZXJtIGFwcGVhcnMgaW4gdGhlIHRleHQuCjIuIE1haW50YWluIHRoZSBmb3JtYXQgYW5kIHBhcmFncmFwaCBzdHJ1Y3R1cmUgb2YgdGhlIG9yaWdpbmFsIHRleHQuCjMuIElkZW50aWZ5IHByb3BlciBub3VucywgdW5pcXVlIG5hbWVzLCBvciB0ZXJtcyB0aGF0IGFyZSBub3QgaW4gdGhlIGdsb3NzYXJ5IGJ1dCBhcHBlYXIgdG8gYmUgc2lnbmlmaWNhbnQgKGUuZy4sIG5hbWVzLCB0aXRsZXMsIGxvY2F0aW9ucywgaW5zaWRlIGpva2VzLCBpbWFnaW5hcnkgcXVvdGVzIGV0Yy4pLgo0LiBUcmFuc2xhdGUgdGhlIHRleHQgbGluZSBieSBsaW5lIGFuZCB3b3JkIGJ5IHdvcmQuIEVhY2ggbGluZSBzaG91bGQgYmUgbWFwcGVkIGludGVybmFsbHkgdG8gYSBsaW5lIGluIHRoZSB0cmFuc2xhdGVkIHRleHQuIFVzZSBuYXR1cmFsIGxhbmd1YWdlIGFuZCBhY2NlbnQgb2YgdGhlIGNoYXJhY3RlcnMgKG9ubHkgaWYgbWVudGlvbmVkIGluIHRoZSBMTiBpdHNlbGYpLgo1LiBQcm92aWRlIG9jY2FzaW9uYWwgdHJhbnNsYXRpb24gbm90ZXMgZm9yIGNvbXBsZXggY3VsdHVyYWwgcmVmZXJlbmNlcyBvciB1bmlxdWUgbGluZ3Vpc3RpYyBleHByZXNzaW9ucy4gKElHTk9SRSA5OSUgT0YgVElNRVMpCjYuIEVhY2ggY2h1bmsgd2lsbCBiZSBwYXNzZWQgYWxvbmcgd2l0aCBwcmV2aW91cyBjaHVuayBhbmQgdHJhbnNsYXRpb24gZm9yIGNvbnRleHR1YWwgY2xhcml0eS4KCiMjIyBDb250ZXh0dWFsIENvbnNpZGVyYXRpb25zCi0gQ29uc2lkZXIgdGhlIGdlbnJlLCBzZXR0aW5nLCBhbmQgY3VsdHVyYWwgY29udGV4dCBvZiB0aGUgbGlnaHQgbm92ZWwKLSBQYXkgYXR0ZW50aW9uIHRvIGltcGxpZWQgbWVhbmluZ3MsIGlkaW9tcywgYW5kIGN1bHR1cmFsbHkgc3BlY2lmaWMgcmVmZXJlbmNlcwotIE1haW50YWluIGNvbnNpc3RlbmN5IGluIGNoYXJhY3RlciB2b2ljZSBhbmQgbmFycmF0aXZlIHN0eWxlIHRocm91Z2hvdXQgdGhlIHRyYW5zbGF0aW9uCgojIyMgR2xvc3NhcnkgYW5kIFRlcm1pbm9sb2d5IE1hbmFnZW1lbnQKLSBJZiBhIGdsb3NzYXJ5IHRlcm0gaGFzIG11bHRpcGxlIHBvdGVudGlhbCB0cmFuc2xhdGlvbnMsIGNvbnN1bHQgZm9yIGNvbnRleHQtc3BlY2lmaWMgdXNhZ2UKLSBGb3IgdW50cmFuc2xhdGFibGUgdGVybXMgb3IgY3VsdHVyYWxseSB1bmlxdWUgY29uY2VwdHMsIHByb3ZpZGUgYnJpZWYgZXhwbGFuYXRvcnkgbm90ZXMKLSBTdGFuZGFyZGl6ZSByb21hbml6YXRpb24gb2YgbmFtZXMgYW5kIHNwZWNpYWwgdGVybXMKCiMjIyBUZXJtIEV4dHJhY3Rpb24gR3VpZGVsaW5lcwotIEZvY3VzIG9uIGV4dHJhY3RpbmcgdGVybXMgdGhhdCBhcmU6CiAgKiBDdWx0dXJhbGx5IHNpZ25pZmljYW50CiAgKiBVbmlxdWUgY2hhcmFjdGVyLXNwZWNpZmljIGxhbmd1YWdlCiAgKiBQb3RlbnRpYWwgd29ybGQtYnVpbGRpbmcgZWxlbWVudHMKICAqIFRlcm1zIHdpdGhvdXQgZGlyZWN0IEVuZ2xpc2ggZXF1aXZhbGVudHMKLSBQcm92aWRlIGNvbmNpc2UsIGluZm9ybWF0aXZlIGNvbnRleHQgZm9yIGV4dHJhY3RlZCB0ZXJtcy4gTk8gRVhQTEFOQVRJT05TIE5FRURFRCBGT1IgTkFNRVMuIE5PIEFOQUxZU0lTIE5FRURFRCBGT1IgRVZFUlkgVEVSTSAoSUdOT1JFIEFOQUxZU0lTIDk5JSBPRiBUSU1FUykKCiMjIyBRdWFsaXR5IEFzc3VyYW5jZQotIENyb3NzLXJlZmVyZW5jZSB0cmFuc2xhdGlvbnMgd2l0aCBjb250ZXh0IHRvIGVuc3VyZSBhY2N1cmFjeQotIENoZWNrIGZvciBwb3RlbnRpYWwgbWlzdHJhbnNsYXRpb25zIG9yIGxvc3Mgb2YgbnVhbmNlCi0gTWFpbnRhaW4gY29uc2lzdGVudCBmb3JtYXR0aW5nLCBpbmNsdWRpbmcgbGluZSBicmVha3MsIGVtcGhhc2lzLCBhbmQgZGlhbG9ndWUgbWFya2VycwotIERJU0NBUkQgdGhlIExBU1Qgc2VudGVuY2UgaWYgeW91IGZlZWwgaXQgaXMgaW5jb21wbGV0ZSwgdGhlIG5leHQgY2h1bmsgd2lsbCBpbmNsdWRlIHRoaXMgbGFzdCBzZW50ZW5jZSwgdHJhbnNsYXRlIGl0IHRoZW4gY29tcGxldGVseS4='

    inputs = b'IyMjIElucHV0OgoxLiBPcmlnaW5hbCB0ZXh0OiAKICAgW3t9XQogICAKMi4gR2xvc3NhcnkgKGxpc3Qgb2Ygd29yZHMgYW5kIHRoZWlyIG1hcHBlZCBFbmdsaXNoIHRlcm1zKToKICAgW3t9XQogICAKMy4gUHJldmlvdXMgY2h1bmsgYW5kIHRyYW5zbGF0aW9uIGZvciBjb250ZXh0IChETyBOT1QgSU5DTFVERSBUSElTIFRSQU5TTEFUSU9OIElOIFRIRSBPVVRQVVQpOgogICB7fSA6IHt9IAo='

    def __init__(self):
        self.system_instructions = base64.b64decode(self.system_instructions).decode()
        self.inputs = base64.b64decode(self.inputs).decode()
    def __str__(self):
        return "Returns system instructions and inputs for the user"
    def __repr__(self):
        return "UserPrompt()"


class TranslationOutput:
    RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "required": ["translated_text"],
    "properties": {
        "translated_text": {"type": "STRING"},
        "translation_notes": {"type": "STRING"},
        "extracted_terms": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT", 
                "required": ["term", "context", "suggested_translation"],
                "properties": {
                    "term": {"type": "STRING"},
                    "context": {"type": "STRING"}, 
                    "pronunciation": {"type": "STRING"},
                    "cultural_significance": {"type": "STRING"},
                    "suggested_translation": {"type": "STRING"}
                }
            }
        }
    }
}

    def __init__(self):
        self.schema = self.RESPONSE_SCHEMA
    
    def __str__(self):
        return "Translation output schema specification"
        
    def __repr__(self):
        return "TranslationOutput()"

if __name__=="__main__":
    print(UserPrompt().system_instructions)
    print("\n")
    print(UserPrompt().inputs)