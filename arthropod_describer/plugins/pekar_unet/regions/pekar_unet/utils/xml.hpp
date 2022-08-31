#pragma once

#include <nlohmann/json.hpp>
#include <rapidxml/rapidxml.hpp>
#include <string>

#include "utils.hpp"


namespace utils::xml
{
inline void addHead(rapidxml::xml_document<> &doc)
{
    auto declaration = doc.allocate_node(rapidxml::node_declaration);
    declaration->append_attribute(doc.allocate_attribute("version", "1.0"));
    declaration->append_attribute(doc.allocate_attribute("encoding", "UTF-8"));
    declaration->append_attribute(doc.allocate_attribute("standalone", "no"));
    doc.insert_node(doc.first_node(), declaration);
}

inline rapidxml::xml_node<> *findNode(const rapidxml::xml_document<> &doc,
                                      const std::string identifier)
{
    for (auto node = doc.first_node("image")->first_node(); node; node = node->next_sibling())
    {
        if (static_cast<std::string>(node->first_node("identifier")->value()) == identifier)
        {
            return node;
        }
    }
    return nullptr;
}

inline void addRegion(rapidxml::xml_document<> &doc, uint label)
{
    auto identifier = std::to_string(label);
    auto region = regions[identifier];

    if (findNode(doc, identifier))
    {
        return;
    }

    auto node = doc.allocate_node(rapidxml::node_element, "region");

    node->append_node(
        doc.allocate_node(rapidxml::node_element, "name",
                          doc.allocate_string(std::string(region["name"]).c_str())));
    node->append_node(doc.allocate_node(rapidxml::node_element, "identifier",
                                        doc.allocate_unsigned_int(label)));
    node->append_node(
        doc.allocate_node(rapidxml::node_element, "colorR",
                          doc.allocate_unsigned_int(region["color"]["red"])));
    node->append_node(
        doc.allocate_node(rapidxml::node_element, "colorG",
                          doc.allocate_unsigned_int(region["color"]["green"])));
    node->append_node(
        doc.allocate_node(rapidxml::node_element, "colorB",
                          doc.allocate_unsigned_int(region["color"]["blue"])));
    doc.first_node("image")->append_node(node);
}

inline void updateMesurement(rapidxml::xml_document<> &doc, int label, rapidxml::xml_node<> *node)
{
    auto region = utils::xml::findNode(doc, std::to_string(label));
    if (region->first_node(node->name()))
    {
        region->remove_node(region->first_node(node->name()));
    }
    region->append_node(node);
}
} // namespace utils::xml