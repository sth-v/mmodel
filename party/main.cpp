//
// Created by Andrew Astakhov on 10.11.22.
//
#include "opennurbs/opennurbs_public.h"
#include "opennurbs/opennurbs_text.h"
#include "opennurbs/opennurbs_font.h"
#include "opennurbs/opennurbs_file_utilities.h"
#include "json/json.h"
#include "json/reader.h"
#include "json/writer.h"
#include "vector"
#include "opennurbs/opennurbs_textobject.h"
#include "opennurbs/opennurbs_textglyph.h"
#include "opennurbs/examples.h"
#include "opennurbs/opennurbs_extensions.h"

ON_Text CreateText(const wchar_t* &text_data,const ON_Font & font, bool & wrapped, const double &width, const float &rot, ON_Plane &plane){
    ON_Text text = ON_Text();

    text.Create(text_data,  &ON_DimStyle::Default, plane, wrapped, width,  rot );
    return text;
}
ON_Text MirrorText(const ON_Text &text){
    ON_Plane mirror_plane = ON_Plane(text.Plane().origin, text.Plane().xaxis, text.Plane().zaxis);
    ON_Text textm=ON_Text(text);
    textm.Transform(ON_Xform::MirrorTransformation(mirror_plane.plane_equation));
    return textm;
}

ON_Geometry AddLayersJ(const char* path, std::vector<ON_Text> &vt){
    auto reader = Json::Reader();
    auto rot = Json::Value("layers");


    auto model = new ONX_Model();

    ON_TextLog log;
    model->Read(path);
    for (int i = 0; i < ; ++i) {
        vt[i].GetTextGlyphContours()
    }
    model->AddModelGeometryComponent()

}


int main(){
    return 0;
}