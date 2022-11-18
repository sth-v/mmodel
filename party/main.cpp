//
// Created by Andrew Astakhov on 10.11.22.
//
#include "iostream"
#include "list"
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
#include "opennurbs/opennurbs_nurbssurface.h"
#include "opennurbs/opennurbs_extensions.h"
#include "python3.10/Python.h"
#include "opennurbs/opennurbs_public.h"
#include "opencascade/gp.hxx"
#include "map"
#include "opencascade/BrepPrimAPI_MakeSweep.hxx"
#include "Metal/Metal.h"
#include "pybind11/include/pybind11/pybind11.h"
#include "pybind11/include/pybind11/numpy.h"
#include "list"
#include "opennurbs/opennurbs_xform.h"
#include "pybind11/include/pybind11/pybind11.h"
#include "pybind11/include/pybind11/stl_bind.h"
#include "pybind11/include/pybind11/numpy.h"

#include "utility"
#include "iostream"
#include "map"

#include "opennurbs/opennurbs_public.h"
#include "opennurbs/opennurbs_nurbssurface.h"
#include "pybind11/include/pybind11/detail/descr.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)


PYBIND11_MAKE_OPAQUE(std::vector<double>);
PYBIND11_MAKE_OPAQUE(std::map<std::string, double>);
PYBIND11_MAKE_OPAQUE(std::vector<std::vector<double>>);
PYBIND11_MAKE_OPAQUE(std::vector<std::map<std::string, double>>);

template<class data_t>

class list
{
    data_t data;
    list *next;
public:
    list(data_t d);
    void add(list *node)
    {
        node->next=this;
        next=0;
    }
    list *getnext(){
        return next;
    }
    data_t getdata(){
        return data;
    }
};


template<class T, class B>
class MMap : std::map<T, B>{
public:
    MMap(const T& owner, const std::string& name): name(name) {}

    void setItem(const T& instance, B& value){
        _table[instance[name]] = value;
    };
    B getItem(const T& key){
        return _table[key] ;
    };
    std::string name;
private:
    std::map<T,B> _table;

};




template<typename yourType,
        template<typename, typename = std::allocator<const yourType*> > class Container>
Container<yourType*> successorsFunction(const yourType& state)
{

}
class CppItem {
public:
    CppItem(const std::map<std::string ,int>& defauts) : name(name) { }
    void setName(const std::string &name_) { name = name_; }
    const std::string &getName() const { return name; }

    std::string name;
};
ON_3dPoint VectorToON_3dPoint(double& x , double& y,double& z){}

class Animal {
public:
    virtual ~Animal() { }
    virtual std::string go(int n_times) = 0;
};

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

ON_Geometry Sweep(const ON_Curve& rail,const ON_Curve& profile){

}

class onPoint3 {
protected:
    double x;
    double y;
    double z;
public:
    onPoint3(double x, double y, double z) : x(x), y(y), z(z) {
        m_xyz=new std::vector<double>{x,y,z};

    }

    std::vector<double> *xyz() { return m_xyz; }
    double get_x() { return _original.x; }
    double get_y() { return _original.y; }
    double get_z() { return _original.z; }
    void set_x(double _x) { _original.x=_x; }
    void set_y(double _y) { _original.y=_y; }
    void set_z(double _z) { _original.z=_z; }
    void xyzSetter(double X, double Y, double Z) {

        set_x(X);set_y(Y);set_z(Z);


    }

    std::vector<double> xyzGetter() {
        return  *xyz();
    }


    double Distance(onPoint3 * other) {
        return this->toON().DistanceTo(other->toON());
    }
    void Transform(ON_Xform& xform) {

        ON_3dPoint on = this->toON();
        on.Transform(xform);
        xyzSetter(on.x, on.y,on.z);
    }
    onPoint3 operator-(onPoint3 *other) const {
        onPoint3 point =onPoint3(this->x-other->x,this->y-other->y,this->z-other->z);
        return point;
    }
    onPoint3 operator+ (onPoint3 *other) const {
        onPoint3 point =onPoint3(this->x+other->x,this->y+other->y,this->z+other->z);
        return point;
    }
    onPoint3 operator/ (onPoint3 *other) const {
        onPoint3 point =onPoint3(this->x /other->x,this->y/other->y,this->z/other->z);
        return point;
    }
    onPoint3 operator* (onPoint3 *other) const {
        onPoint3 point =onPoint3(this->x*other->x,this->y*other->y,this->z*other->z);
        return point;
    }

    ON_3dPoint toON() {
        return ON_3dPoint(this->x, this->y, this->z);
    }
    std::string jsonRepr() {

        return "[" + std::to_string(x) + "," + std::to_string(y) + "," + std::to_string(z) + "]";

    }


private:

    std::vector<double> *m_xyz{};
    ON_3dPoint _original{};

};


class  ON_3Plane :ON_Plane {
protected:
    ON_Plane original_plane;
    onPoint3 old_origin;
    ON_3dPoint origin{};
    ON_3dVector xaxis;
    ON_3dVector yaxis{};
    ON_3dVector normal;
    ON_PlaneEquation plane_equation ;
    ON_Xform xform;

public:
    ON_3Plane(onPoint3 origin, ON_3dVector normal, ON_3dVector xaxis) :  old_origin(origin) ,normal(normal), xaxis(xaxis) {
        yaxis = ON_3dVector::CrossProduct(xaxis,zaxis);
        original_plane=ON_Plane(this->Origin(), this->XAxis(), this->Yaxis());
        original_plane.UpdateEquation();

    }


    ON_3dPoint Origin(){
        return origin;
    }
    ON_3dPoint SetOrigin(onPoint3& _origin){
        origin = old_origin.toON();
        this->UpdateEquation();

    }
    ON_3dVector Normal(){
        return normal;
    }
    ON_3dVector SetNormal(ON_3dVector& _normal){
        normal = _normal;
        this->UpdateEquation();
    }
    ON_3dVector XAxis(){
        return xaxis;

    }
    ON_3dVector XAxisSetter(ON_3dVector& _xaxis){

        this->UpdateEquation();
    }
    int Transform(const ON_Xform &xform) {
        return ON_Plane::Transform(xform);
    }
    bool ClosestPointTo(ON_3dPoint world_point,double* u,double* v){
        return original_plane.ClosestPointTo(world_point, u, v);
    }

};


namespace py = pybind11;
PYBIND11_MODULE(nurbstools, m) {
    py::bind_vector<std::vector<double>>(m, "VectorDouble");
    py::bind_map<std::map<std::string, double>>(m, "MapStringDouble");
    py::bind_vector<std::vector<std::vector<double>>>(m, "VectorVectorDouble");
    py::bind_vector<std::vector<std::map<std::string, double>>>(m, "VectorMapStringDouble");
    py::bind_map<std::map<std::string, PyObject>>(m, "ItemKwargs");


    py::class_<onPoint3>(m, "ON_3dPoint", py::buffer_protocol())
        .def(py::init<double ,double , double >())
        .def_buffer([](onPoint3 &m) -> py::buffer_info {
                        return py::buffer_info(
                                m.xyz(),                               /* Pointer to buffer */
                                sizeof(float),                          /* Size of one scalar */
                                py::format_descriptor<float>::format(), /* Python struct-style format descriptor */
                                1,                                      /* Number of dimensions */
                                { m.get_x(), m.get_y(), m.get_z()},                 /* Buffer dimensions */
                                { sizeof(float) * 3}
                        );
                    }
        )
        .def_property("xyz", &onPoint3::xyzGetter, &onPoint3::xyzSetter)
        .def_property("x", &onPoint3::get_x, &onPoint3::set_x)
        .def_property("y", &onPoint3::get_y, &onPoint3::set_y)
        .def_property("z", &onPoint3::get_z, &onPoint3::set_z)
        .def("distance",&onPoint3::Distance)
        .def("Transform",&onPoint3::Transform) ;

    py::class_<ON_Plane>(m, "ON_3Plane")
        .def("transform", &ON_Plane::Transform);
    std::make_shared<ON_Xform>();
    py::class_<ON_Xform>(m, "ON_3dPoint", py::buffer_protocol())
        .def_buffer([](ON_Xform& m) -> py::buffer_info {
                            return py::buffer_info(m.m_xform, ssize_t(16), false);
        });};