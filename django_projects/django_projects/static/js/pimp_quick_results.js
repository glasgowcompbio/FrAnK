$(document).ready(function() {
  let identifiedPeaksPKs,
      identifiedMetaboliteSecondaryIds;

  function initPeaksTable(data) {
    const originalNumPeaks = data.length;
    $('#num-peaks').text(originalNumPeaks);

    var peaksTableAPI = $('#peak-table2').DataTable({
      "data": data,
      "columns": [
        {"name": "peakPK", "title": "peakPK", "visible": false, "data": "peakPK"},
        {"name": "secondaryID", "title": "ID", "data": "peakSecondaryId"},
        {"name": "mass", "title": "mass", "data": "mass"},
        {"name": "rt", "title": "RT", "data": "rt"},
        {"name": "identified", "data": null, "orderable": false, "className": "not-selectable", "render": function(data, type, row, meta) {
          if (identifiedPeaksPKs.includes(row.peakPK)) {
            return '<img src="' + pimpIdLogoUrl + '" width="20" height="20" draggable="false" data-toggle="tooltip" title="Identified">';
          } else {
            return "";
          }
        }}
      ],
      "dom": "rtp",
      "select": {
        "items": "row",
        "style": "single",
        "selector": "td:not(.not-selectable)"
      },
      "rowId": "peakPK",
      "paging" : false,
      "pagingType": "simple",
      "scrollY": "40vh",
      "scrollCollapse": false,
      "drawCallback": function(settings, json) {
        const api = this.api();
        $('#num-peaks-filtered').text(api.rows().count());
      }
    });

    return peaksTableAPI;
  };

  function initMetabolitesTable(data) {
    var data = alasql("SELECT DISTINCT metaboliteSecondaryId, metaboliteName FROM ?", [data]);

    originalNumMetabolites = data.length,
    $('#num-metabolites').text(originalNumMetabolites);

    var metabolitesTableAPI = $('#metabolite-table2').DataTable({
      "data": data,
      "columns": [
        // {"name": "metabolitePK", "title": "metabolitePK", "visible": false, "data": "metabolitePK"},
        {"name": "metaboliteSecondaryId", "title": "metaboliteSecondaryId", "visible": false, "data": "metaboliteSecondaryId"},
        {"name": "metaboliteName", "title": "Name", "visible": true, "data": "metaboliteName"},
        {"name": "identified", "visible": true, "data": "identified", "orderable": false, "className": "not-selectable", "render": function(data, type, row, meta) {
          if (identifiedMetaboliteSecondaryIds.includes(row.metaboliteSecondaryId)) {
            return '<img src="' + pimpIdLogoUrl + '" width="20" height="20" draggable="false" data-toggle="tooltip" title="Identified">';
          } else {
            return "";
          }
        }}
      ],
      "dom": "rtp",
      "select": {
        "items": "row",
        "style": "single",
        "selector": "td:not(.not-selectable)"
      },
      "rowId": "metaboliteSecondaryId",
      "paging": false,
      "pagingType": "simple",
      "scrollY": "40vh",
      "scrollCollapse": false,
      "drawCallback": function(settings, json) {
        const api = this.api();
        $('#num-metabolites-filtered').text(api.rows().count());
      }
    });

    return metabolitesTableAPI;
  };

  function initPathwaysTable(data) {
    const originalNumPathways = data.length;
    $('#num-pathways').text(originalNumPathways);

    var pathwaysTableAPI = $('#pathway-table2').DataTable({
      "data": data,
      "columns": [
        {"name": "pathwayPK", "title": "pathwayPK", "visible": false, "data": "pathwayPK"},
        {"name": "pathwayName", "title": "Name", "data": "pathwayName"}
      ],
      "dom": "rtp",
      "select": {
        "style": "single"
      },
      "rowId": "pathwayPK",
      "paging": false,
      "pagingType": "simple",
      "scrollY": "40vh",
      "scrollCollapse": false,
      "drawCallback": function(settings, json) {
        const api = this.api();
        $('#num-pathways-filtered').text(api.rows().count());
      }
    });

    return pathwaysTableAPI;
  };

  // Section: Functions to populate the object information panes
  function getPeakInfo(peakObject) {
    clearPeakInfo();

    // Update the peak information column---------------------------------
    const ppm = 3;
    let peakInfo = {'pk': peakObject.peakPK, 'ppm': ppm, 'rtwindow': 120, 'id': peakObject.peakSecondaryId}

    $.getJSON(get_peak_info_url, peakInfo, function(data) {
      peakInfoPanelBody.append('<p>Type: ' + data['type'] + '</p>');
      peakInfoPanelBody.append('<p>Polarity: ' + data['polarity'] + '</p>');
    });

    let peak_info_title = $('<h5/>', {
      'text': 'Peak # ' + peakInfo['id']
    });

    let peakInfoPanelBody = $('#peak-row-info .panel-body').empty();
    peakInfoPanelBody.append(peak_info_title);
    // Make a list-group to organise the plots
    let peak_info_list_group = $('<ul/>', {
      'class': 'list-group'
    });

    // Prepare chromatogram element
    let chromatogram_load_btn = $('<button/>', {
      'class': 'btn btn-sm btn-default chromatogram_load_btn',
      'text': 'Load chromatogram'
    });

    let chromatogram_li = $('<li/>', {
      'class': 'list-group-item',
      'id': 'chromatogram-li',
      'html': chromatogram_load_btn
    });
    peak_info_list_group.append(chromatogram_li);

    // Prepare d3 intensity chart element
    let d3_intensity_chart_load_btn = $('<button/>', {
      'class': 'btn btn-sm btn-default d3_intensity_chart_load_btn',
      'text': 'Load d3 intensity chart'
    });

    let d3_intensity_chart_li = $('<li/>', {
      'class': 'list-group-item',
      'id': 'd3-intensity-chart-li',
      'html': d3_intensity_chart_load_btn
    });
    peak_info_list_group.append(d3_intensity_chart_li);

    $('#peak-row-info .panel').append(peak_info_list_group);

    // Provide buttons to load chromatograms and intensity charts on demand
    // because they are slow to load
    chromatogram_load_btn.click(function() {
      $(this).text("Loading chromatogram...");
      $(this).attr("disabled", "disabled");
      $.getJSON(chromatogram_url, peakInfo, function(data) {
        const chartWidth = $('#peak-row-info .panel-body').width();
        createPeaksChromatogram(chartWidth, chromatogram_li, ppm, data);
      });
    })

    d3_intensity_chart_load_btn.click(function() {
      $(this).text("Loading intensity chart...");
      $(this).attr("disabled", "disabled");
      plotPeakIntensitySamples(peakInfo, 'd3-intensity-chart-li');
    });
  }

  function getMetaboliteInfo(metaboliteObject) {
    // metaboliteRowData should be the selected metabolite table row data as an array
    // in the order that they appear in the table
    // Consider changing this to objects to avoid indexing by number/position (its not generalised)
    clearMetaboliteInfo();
    const res = alasql("SELECT metabolitePK, metaboliteName FROM Metabolites WHERE metaboliteSecondaryId = ?", metaboliteObject['metaboliteSecondaryId']),
          // Multiple primary keys associate with one secondary Id, so pick the first: they should be the same compound.
          metaboliteInfo = {'id': res[0]['metabolitePK']};

    let metabolite_info_div = $('<div/>', {
      'id': 'metabolite_info_div'
    });

    let metabolite_info_title = $('<h5/>', {
      'text': metaboliteObject['metaboliteName']
    });

    metabolite_info_div.append(metabolite_info_title);

    let keggStructureDom = $('<div\>', {
      'html': '<p>Loading chemical structure...</p>'
    });

    $.getJSON(get_kegg_metabolite_info, metaboliteInfo, function(data) {
      metabolite_info_div.append('<p>Inchikey: ' + data['inchikey'] + '</p>');
      metabolite_info_div.append('<p>ppm: ' + data['ppm'] + '</p>');
      metabolite_info_div.append('<p>Adduct: ' + data['adduct'] + '</p>');
      let keggStructureImg = $('<img/>', {
        'src': 'http://www.kegg.jp/Fig/compound/' + data['kegg_id'] + '.gif',
        'class': 'img-responsive'
      });
      keggStructureDom.empty().append(keggStructureImg);
      keggStructureDom.append($('<p/>').append($('<a/>', {
        'href': 'http://www.genome.jp/dbget-bin/www_bget?cpd:' + data['kegg_id'],
        'target': '_blank',
        'text': 'Link to KEGG compound database'
      })));
    });

    $('#metabolite-row-info .panel-body').empty();
    $('#metabolite-row-info .panel-body').append(metabolite_info_div);
    $('#metabolite-row-info .panel-body').append(keggStructureDom);

  }

  function getPathwayInfo(pathwayObject) {
    clearPathwayInfo();
    const pathwayName = pathwayObject['pathwayName'],
          pathwayInfo = {'id': pathwayObject['pathwayPK']};

    var pathway_info_title = $('<h5/>', {
      'text': pathwayName
    });

    var pathwayInfoPane = $('#pathway-row-info .panel-body').empty();
    pathwayInfoPane.append(pathway_info_title);

    $.getJSON(get_pathway_info, pathwayInfo, function(data) {
      pathwayInfoPane.append($('<p/>').append($('<a/>', {
        'href': 'http://www.genome.jp/dbget-bin/www_bget?' + data['pathway_id'],
        'target': '_blank',
        'text': 'Link to KEGG compound database'
      })));
    });
  }

  function createPeaksChromatogram(chartWidth, div, ppm, response) {
    polarity = response[0][0]
    retentionTime = response[0][1]
    mass = response[0][2]
    // Begining of chart
    $(div).highcharts({
      credits : {
        enabled : false
        },
      chart: {
        zoomType: 'x',
        // spacingRight: 20,
        width: chartWidth,
        height: 400,
        backgroundColor: '#FFFFFF',
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
        events: {
          click: function (event) {
            event.preventDefault();
            if(($(event.target)[0].textContent) != "Reset zoom"){
              peaksChromatogramPopUp(mass, retentionTime, response);
            }
          }
        }
      },
      title: {
        text: 'Peak chromatogram'
      },
      subtitle: {
        text: 'Mass: '+parseFloat(mass).toFixed(4)+' ppm: '+ppm
      },
      exporting: {
        enabled: true,
      },
      xAxis: {
        title: {
          text: 'Retention time (s)'
        },
        showLastLabel: true
      },
      yAxis: {
        title: {
          text: 'Measured abundance'
        },
        min: 0,
      },
      tooltip: {
        shared: true,
        headerFormat: '',
        pointFormat: '<span style="font-size: 10px;font-weight: bold;color:{point.series.color}">{series.name}</span><br/>Retention time: {point.x}<br/>Intensity: {point.y}<br/>'
      },
      legend: {
        enabled: true
      },
      plotOptions: {
        area: {
          marker: {
            enabled: false,
            symbol: 'circle',
            radius: 2,
            states: {
              hover: {
                enabled: true
              }
            }
        },
        lineWidth: 1,
        shadow: false,
        states: {
          hover: {
            lineWidth: 1
          }
        },
        threshold: null
        },
        series: {
          fillOpacity: 0.1
        }
      },
      series: [{
          type: 'area',
          name: response[1][0],
          data : response[1][1]
      }]
    });
    for (var i=2;i<response.length;i++) {
      $(div).highcharts().addSeries({
        type: 'area',
        name: response[i][0],
        data : response[i][1]
        });
      }
      for (var i=0;i<$(div).highcharts().series.length;i++) {
        if ($(div).highcharts().series[i].data.length == 0) {
          $(div).highcharts().series[i].hide();
        }
      }
    // End of chart
  }

  function compare(a,b) {
    if (a.index < b.index) {
       return -1;
    }
    if (a.index > b.index) {
      return 1;
    }
    return 0;
  }

  function plotPeakIntensitySamples(peakInfo, chartDivID) {
    var dataStore = [];
    $.getJSON(get_peak_intensities_url, peakInfo, function(data) {
      // console.log(data);
      var maxOverallIntensity = 0,
          attributes = Object.keys(data);

      attributes.forEach(function(attribute, i) {
        var attributeSamples = data[attribute],
            intensities = d3.values(attributeSamples),
            sampleNames = Object.keys(attributeSamples),
            maxAttributeIntensity = d3.max(intensities),
            sortedIntensities = d3.values(attributeSamples).sort(d3.ascending),
            boxPlotStatistics = {
              lowerquantile: d3.quantile(sortedIntensities, 0.25),
              median: d3.quantile(sortedIntensities, 0.5),
              upperquantile: d3.quantile(sortedIntensities, 0.75),
              mini: d3.min(sortedIntensities),
              maxi: d3.max(sortedIntensities)
            },
            points = [];

        maxOverallIntensity = (maxOverallIntensity > maxAttributeIntensity ? maxOverallIntensity : maxAttributeIntensity);

        // Make x y coordinates
        intensities.forEach(function(d, i) {
          points.push({
            x: attribute,
            y: d,
            z: sampleNames[i],
          });
        });

        dataStore.push({
          attributeName: attribute,
          boxPlotStatistics: boxPlotStatistics,
          points: points
        });
      });

      console.log('d3 munged data', dataStore);

      // d3 margin convention. Make the width and height relative to page components
      var margin = {top: 20, bottom: 75, right: 20, left: 60},
          width = $('#peak-row-info .panel-body').width() - margin.right - margin.left,
          height = $('#results-table-row').height() - margin.top - margin.bottom;

      $('#' + chartDivID).empty();

      // Initialise the svg
      var svg = d3.select("body")
        .select('#' + chartDivID)
        .append("svg")
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .classed("d3-intensity-chart", true);

      // Make the graphing area
      var graph = svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      // set the x and y scale functions
      var yScale = d3.scaleLinear()
        .domain([0, maxOverallIntensity*1.1]) // add some extra space at the top of the y axis with *1.1
        .range([height, 0]);
      var xScale = d3.scalePoint()
        .domain(attributes)
        .range([0, width])
        .round(true)
        .padding(0.5);

      // x axis
      graph.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(xScale))
        .selectAll("text")
        .attr('y', -5) // rotate and adjust tick positions
        .attr('x', -30)
        .attr('transform', 'rotate(270)');

      // y axis
      graph.append('g')
        .call(d3.axisLeft(yScale)
        .ticks(5, 'e')); // scientific notation

      // y axis label
      svg.append("text")
        .text('Relative intensity')
        .attr('transform', 'translate(' + margin.left/6 +  ',' + (height*0.75) + ') rotate(270)');

      // make a group for each
      var pointStep = xScale.step(),
          horizontalLineWidth = pointStep/4;

      // Functions for mouseover
      function displaySampleName(d, i) {
        var circle = d3.select(this);
        d3.select(this)
          .attr('fill', 'blue')
          .attr('r', 10);

        svg.append('text')
          .attr('id', function() { return 'sample-name-text-' + d.z.split('.')[0]; })
          .attr('x', (width + margin.top + margin.bottom) / 2)
          .attr('y', margin.top)
          .text(function() { return d.z.split('.')[0]; });
      }

      function hideSampleName(d, i) {
        d3.select(this)
          .attr('fill', 'black')
          .attr('r', 3);

        d3.select('#sample-name-text-' + d.z.split('.')[0]).remove();
      }

      var dataSeriesGroups = graph.selectAll('g .data-series-group')
        .data(dataStore)
        .enter()
        .append('g')
        .attr('class', 'data-series-group')
        .attr('id', function(d) { return 'data-series-' + d.attribute; });

      dataSeriesGroups.each(function(attribute, i) {
        var coordinates = attribute.points;
        var boxPlotStatistics = [attribute.boxPlotStatistics],
          g = d3.select(this);

        // Add circles for each data point
        g.selectAll('circle')
          .data(coordinates)
          .enter()
          .append('circle')
          .attr('cx', function(d) { return xScale(d.x); })
          .attr('cy', function(d) { return yScale(d.y); })
          .attr('r', 3)
          .attr('sample-name', function(d) { return d.z; })
          .on('mouseover', displaySampleName)
          .on('mouseout', hideSampleName);

        // Median line
        g.selectAll('line .median-line')
          .data(boxPlotStatistics)
          .enter()
          .append('line')
          .attr('class', 'median-line')
          .attr('x1', xScale(attribute.attributeName) -  horizontalLineWidth)
          .attr('x2', xScale(attribute.attributeName) +  horizontalLineWidth)
          .attr('y1', function(d) { return yScale(d.median); })
          .attr('y2', function(d) { return yScale(d.median); })
          .attr('stroke', 'black');

        // Quantile box
        g.selectAll('rect .quantile-box')
          .data(boxPlotStatistics)
          .enter()
          .append('rect')
          .attr('class', 'quantile-box')
          .attr('x', xScale(attribute.attributeName) - horizontalLineWidth)
          .attr('y', function(d) { return yScale(d.upperquantile); })
          .attr('width', horizontalLineWidth*2)
          .attr('height', function(d) { return (yScale(d.lowerquantile) - yScale(d.upperquantile)); })
          .attr('stroke', 'black')
          .style('fill', 'none');

        // horizontal line for upper whisker
        g.selectAll('line .upper-whisker-horizontal-line')
          .data(boxPlotStatistics)
          .enter()
          .append('line')
          .attr('class', 'upper-whisker-line')
          .attr('x1', function(d) { return xScale(attribute.attributeName) -  horizontalLineWidth; })
          .attr('x2', function(d) { return xScale(attribute.attributeName) +  horizontalLineWidth; })
          .attr('y1', function(d) { return yScale(d.maxi); })
          .attr('y2', function(d) { return yScale(d.maxi); })
          .attr('stroke', 'black');

        // vertical line for upper whisker
        g.selectAll('line .upper-whisker-vertical-line')
          .data(boxPlotStatistics)
          .enter()
          .append('line')
          .attr('class', '.upper-whisker-vertical-line')
          .attr('x1', function(d) { return xScale(attribute.attributeName); })
          .attr('x2', function(d) { return xScale(attribute.attributeName); })
          .attr('y1', function(d) { return yScale(d.lowerquantile); })
          .attr('y2', function(d) { return yScale(d.mini); })
          .attr('stroke', 'black');


        // horizontal line for lower whisker
        g.selectAll('line .lower-whisker-horizonal-line')
          .data(boxPlotStatistics)
          .enter()
          .append('line')
          .attr('class', 'upper-lower-line')
          .attr('x1', function(d) { return xScale(attribute.attributeName) -  horizontalLineWidth; })
          .attr('x2', function(d) { return xScale(attribute.attributeName) +  horizontalLineWidth; })
          .attr('y1', function(d) { return yScale(d.mini); })
          .attr('y2', function(d) { return yScale(d.mini); })
          .attr('stroke', 'black');

        // vertical line for lower whisker
        g.selectAll('line .lower-whisker-vertical-line')
          .data(boxPlotStatistics)
          .enter()
          .append('line')
          .attr('class', '.lower-whisker-vertical-line')
          .attr('x1', function(d) { return xScale(attribute.attributeName); })
          .attr('x2', function(d) { return xScale(attribute.attributeName); })
          .attr('y1', function(d) { return yScale(d.upperquantile); })
          .attr('y2', function(d) { return yScale(d.maxi); })
          .attr('stroke', 'black');
      });
    });
  }

  function clearPeakInfo() {
    // Create the divs that make up the 'blank' peak info panel
    var peak_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
    var peak_row_info_title = $('<div/>', {'class': 'panel-heading'});
    var peak_row_info_title_content = $('<h1/>', {
      'class': 'panel-title',
      'id': 'peak-panel-title',
      'text': 'Peak Information'
    });
    var peak_row_info_body_blank = $('<div/>', {
      'text': 'Click a peak above for more information',
      'class': 'panel-body'
    });

    // Combine them
    // Put the title content into the panel title
    peak_row_info_title.append(peak_row_info_title_content)
    // Put the title into the parent panel
    peak_row_info_panel.append(peak_row_info_title)
    // Put the body content into the parent panel
    peak_row_info_panel.append(peak_row_info_body_blank);

    $('#peak-row-info').empty().append(peak_row_info_panel);

  }

  function clearMetaboliteInfo() {
    // Create the divs that make up the 'blank' metabolite info panel
    var metabolite_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
    var metabolite_row_info_title = $('<div/>', {'class': 'panel-heading'});
    var metabolite_row_info_title_content = $('<h1/>', {
      'class': 'panel-title',
      'id': 'metabolite-panel-title',
      'text': 'Metabolite Information'
    });
    var metabolite_row_info_body_blank = $('<div/>', {
      'text': 'Click a metabolite above for more information',
      'class': 'panel-body'
    });

    // Combine them
    // Put the title content into the panel title
    metabolite_row_info_title.append(metabolite_row_info_title_content)
    // Put the title into the parent panel
    metabolite_row_info_panel.append(metabolite_row_info_title)
    // Put the body content into the parent panel
    metabolite_row_info_panel.append(metabolite_row_info_body_blank);

    $('#metabolite-row-info').empty().append(metabolite_row_info_panel);
  }

  function clearPathwayInfo() {
    // Create the divs that make up the 'blank' pathway info panel
    var pathway_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
    var pathway_row_info_title = $('<div/>', {'class': 'panel-heading'});
    var pathway_row_info_title_content = $('<h1/>', {
      'class': 'panel-title',
      'id': 'pathway-panel-title',
      'text': 'Pathway Information'
    });
    var pathway_row_info_body_blank = $('<div/>', {
      'text': 'Click a pathway above for more information',
      'class': 'panel-body'
    });

    // Combine them
    // Put the title content into the panel title
    pathway_row_info_title.append(pathway_row_info_title_content)
    // Put the title into the parent panel
    pathway_row_info_panel.append(pathway_row_info_title)
    // Put the body content into the parent panel
    pathway_row_info_panel.append(pathway_row_info_body_blank);

    $('#pathway-row-info').empty().append(pathway_row_info_panel);
  }

  $.getJSON(quick_results_data_url, function(data) {
    // Make SQL tables
    let peaks = data['peaks'],
        metabolitesPeaks = data['metabolites_peaks'],
        metabolites = data['metabolites_names'],
        pathwaysMetabolites = data['pathways_metabolites'],
        pathways = data['pathways_names'],
        peaksComparisonsList = data['peaks_comparisons_list'],
        comparisonsAttributesMap = data['comparisons_attributes_map'],
        comparisonIds = [],
        alpha = 0.05;

    // Create comparison dropdown
    $('#comparison-select').empty();
    $('#comparison-select').append($('<option/>', {
      'text': 'All comparisons',
      'id': 'select-comparison-all'
    }));
    comparisonsAttributesMap.forEach(function(d, i) {
      const comparison = $('<option/>', {
        'text': d[1] + ' / ' + d[0],
        'id': 'select-comparison-' + d.comparison_id
      });
      $('#comparison-select').append(comparison);
      comparisonIds.push(d.comparison_id);
    });

    // P-value significance with comparisons
    let peaksComparisonSignificance = [];
    const pks = Object.keys(peaksComparisonsList);
    for (let idx = 0; idx < pks.length; idx++) {
      let pk = pks[idx],
          peakComparisonData = peaksComparisonsList[pk],
          pValues = peakComparisonData['pValue'],
          adjPValues = peakComparisonData['adjPValue'],
          pValueSignificant = "False",
          adjPValueSignificant = "False",
          peakComparisonSignificance = {};

      // Make datastructure to store significance status for each peak and comparison
      comparisonIds.forEach(function(comparisonId, idx) {
        peakComparisonSignificance[comparisonId] = {
          'peakPK': +pk,
          'comparisonId': comparisonId,
          'pValue': pValueSignificant,
          'adjPValue': adjPValueSignificant
        };
      });

      // Compare each p value for each comparison with alpha
      comparisonIds.forEach(function(comparisonId, idx) {
        if (pValues[comparisonId] < alpha) {
          peakComparisonSignificance[comparisonId]['pValue'] = "True";
        }
        if (adjPValues[comparisonId] < alpha) {
          peakComparisonSignificance[comparisonId]['adjPValue'] = "True";
        }
      });

      // Add to the main datastructure
      comparisonIds.forEach(function(comparisonId) {
        peaksComparisonSignificance.push(peakComparisonSignificance[comparisonId]);
      });

    }

    alasql("CREATE TABLE Peaks");
    alasql.tables.Peaks.data = peaks;

    alasql("CREATE TABLE PeaksComparisonSignificance");
    alasql.tables.PeaksComparisonSignificance.data = peaksComparisonSignificance;

    alasql("CREATE TABLE Metabolites");
    alasql.tables.Metabolites.data = metabolites;

    alasql("CREATE TABLE MetabolitesPeaks");
    alasql.tables.MetabolitesPeaks.data = metabolitesPeaks;

    alasql("CREATE TABLE PathwaysMetabolites");
    alasql.tables.PathwaysMetabolites.data = pathwaysMetabolites;

    alasql("CREATE TABLE Pathways");
    alasql.tables.Pathways.data = pathways;

    const identifiedPeaksPKsObjects = alasql("SELECT peakPK FROM MetabolitesPeaks WHERE identified = 'True'");
    identifiedPeaksPKs = identifiedPeaksPKsObjects.map(function(peak) {
      return peak.peakPK;
    })

    const identifiedMetaboliteSecondaryIdsObjects = alasql("SELECT metaboliteSecondaryId FROM MetabolitesPeaks WHERE identified = 'True'");
    identifiedMetaboliteSecondaryIds = identifiedMetaboliteSecondaryIdsObjects.map(function(metabolite) {
      return metabolite.metaboliteSecondaryId;
    })

    // Populate datatables
    let peaksTableAPI = initPeaksTable(peaks),
        metabolitesTableAPI = initMetabolitesTable(metabolites),
        pathwaysTableAPI = initPathwaysTable(pathways);

    // Get the initial datatables IDs
    let peaksPKs = peaks.map(function(d) {
      return d.peakPK;
    });

    let metabolitesSecondaryIds = metabolites.map(function(d) {
      return d.metaboliteSecondaryId;
    });

    metabolitesSecondaryIds = metabolitesSecondaryIds.filter(function(d, i, arr) {
      return arr.indexOf(d) === i;
    });

    let pathwaysPKs = pathways.map(function(d) {
      return d.pathwayPK;
    });

    let defaultConstraints = {
      'peak-table2': peaksPKs,
      'metabolite-table2': metabolitesSecondaryIds,
      'pathway-table2': pathwaysPKs,
      'identified': ["True", "False"],
      'pValueCorrected': ["True", "False"],
      'adjPValueCorrected': ["True", "False"],
      'comparisonId': comparisonIds
    };

    let constraints = {
      'peak-table2': defaultConstraints['peak-table2'],
      'metabolite-table2': defaultConstraints['metabolite-table2'],
      'pathway-table2': defaultConstraints['pathway-table2'],
      'identified': defaultConstraints['identified'],
      'pValueCorrected': defaultConstraints['pValueCorrected'],
      'adjPValueCorrected': defaultConstraints['adjPValueCorrected'],
      'comparisonId': defaultConstraints['comparisonId']
    };

    function resetTableConstraints() {
      // reset the stack
      stack.stack = [];
      constraints['peak-table2'] = defaultConstraints['peak-table2'];
      constraints['metabolite-table2'] = defaultConstraints['metabolite-table2'];
      constraints['pathway-table2'] = defaultConstraints['pathway-table2'];

      $('#peak-table2 .selected').removeClass('selected');
      $('#metabolite-table2 .selected').removeClass('selected');
      $('#pathway-table2 .selected').removeClass('selected');
    }

    function Stack() {
      this.stack = [],
      this.addToStack = function(name) {
        let nameIdx;
        // Find if name is in the stack
        this.stack.forEach(function(d, i) {
          if (d === name) {
            nameIdx = i;
          }
        })
        // If the name is in the stack, remove it
        if (nameIdx) {
          this.stack.splice(nameIdx, 1);
        }
        // Add name to the stack
        this.stack.push(name);
      },
      this.removeFromStack = function(name) {
        let nameIdx;
        this.stack.forEach(function(d, i) {
          if (d == name) {
            nameIdx = i;
          }
        })
        this.stack.splice(nameIdx, 1);
      }
    }

    let stack = new Stack();

    $('#p-value-adjust-options :input').change(changePValueFilter);

    function changePValueFilter() {
      resetTableConstraints();
      clearPeakInfo();
      clearMetaboliteInfo();
      clearPathwayInfo();

      const pValueFilter = $('#p-value-adjust-options label.active > input').attr('data-pvaladjustment');
      if (pValueFilter === 'none') {
        constraints.pValueCorrected = ["True", "False"];
        constraints.adjPValueCorrected = ["True", "False"];
        // Clear the comparison filter
        $('#comparison-select').val('All comparisons');
        constraints['comparisonId'] = comparisonIds;
        $('#comparison-select-row').hide();
      } else if (pValueFilter === 'uncorrected') {
        constraints.pValueCorrected = ["True"];
        constraints.adjPValueCorrected = ["True", "False"];
        $('#comparison-select-row').show();
      } else if (pValueFilter === 'corrected') {
        constraints.pValueCorrected = ["True"];
        constraints.adjPValueCorrected = ["True"];
        $('#comparison-select-row').show();
      }
      updateTables();
    };

    $('#annotation-type-options :input').change(changeIdentificationFilter);

    function changeIdentificationFilter() {
      resetTableConstraints();
      clearPeakInfo();
      clearMetaboliteInfo();
      clearPathwayInfo();

      const annotation_type = $('#annotation-type-options label.active > input').attr('data-identified');
      if (annotation_type === 'all') {
        constraints.identified = ['True', 'False'];
      } else {
        constraints.identified = [annotation_type];
      }
      updateTables();
    }

    $('#custom-set-btn').click(changeCustomSet);

    function changeCustomSet() {
      // Changes default constraints to user-specified set until user resets to initial default constraints?
      // Get the table to apply the filter to
      const tableId = $('#custom-set-selector :selected').attr('data-table');
      // Get raw input
      const rawInput = $('#custom-set-textarea').val().split('\n');
      // Munge
      const values = rawInput.map(function(rawValue) {
        if (tableId === 'peak-table2') {
          return +rawValue;
        } else {
          return rawValue;
        }
      });
      // Convert the values to their primary keys
      let queryRes = alasql(tableIdToSqlQueryForSets[tableId], [values]);
      const constraints = queryRes.map(function(res) {
        return res[tableIdToIdColumnMap[tableId]];
      })
      // Set the defaultConstraints to the new set
      defaultConstraints[tableId] = constraints;

      resetTableConstraints();
      updateTables();
    }

    const tableIdToSqlQueryForSets = {
      'peak-table2': "SELECT DISTINCT peakPK FROM Peaks WHERE peakSecondaryId IN @(?)",
      'metabolite-table2': "SELECT DISTINCT metaboliteSecondaryId FROM Metabolites WHERE metaboliteName IN @(?)",
    };

    $('#clear-sets-btn').click(clearSets);

    function clearSets() {
      // Restores the default sets for each constraint, deleting the user-specified
      // sets. Then, resets the stack constraints and redraws the tables.
      defaultConstraints['peak-table2'] = peaksPKs;
      defaultConstraints['metabolite-table2'] = metabolitesSecondaryIds;
      defaultConstraints['pathway-table2'] = pathwaysPKs;
      $('#custom-set-textareas textarea').each(function() {
        $(this).val('');
      })
      resetTableConstraints();
      updateTables();
    }

    $('#comparison-select').change(changeComparisonConstraint);

    function changeComparisonConstraint() {
      const comparisonId = $(this).children(':selected').prop('id').split('-')[2];
      if (comparisonId === 'all') {
        constraints['comparisonId'] = comparisonIds;
      } else {
        constraints['comparisonId'] = [+comparisonId];
      }

      resetTableConstraints();
      updateTables();
    }

    $('.export-data').click(exportData);

    function exportData() {
      const tableId = $(this).prop('id') + "2",
            tables = $('.dataTable').DataTable(),
            tableAPI = tables.table('#' + tableId),
            dat = tableAPI.data().toArray();

      alasql("SELECT * INTO TAB('" + tableId + ".tsv') FROM ?", [dat]);
    }

    const compiledMasterQuery = alasql.compile("SELECT DISTINCT p.peakPK, p.peakSecondaryId, p.mass, p.rt, \
    m.metaboliteName, m.metaboliteSecondaryId, mp.identified, \
    pw.pathwayPK, pw.pathwayName \
    FROM Peaks AS p \
    INNER JOIN PeaksComparisonSignificance AS ps ON p.peakPK = ps.peakPK \
    INNER JOIN MetabolitesPeaks AS mp ON p.peakPK = mp.peakPK \
    INNER JOIN Metabolites AS m ON mp.metaboliteSecondaryId = m.metaboliteSecondaryId \
    INNER JOIN PathwaysMetabolites as pwm ON m.metaboliteSecondaryId = pwm.metaboliteSecondaryId \
    INNER JOIN Pathways as pw ON pwm.pathwayPK = pw.pathwayPK \
    WHERE p.peakPK IN @(?) \
    AND m.metaboliteSecondaryId IN @(?) \
    AND pw.pathwayPK IN @(?) \
    AND mp.identified IN @(?) \
    AND ps.pValue IN @(?) \
    AND ps.adjPValue IN @(?) \
    AND ps.comparisonId IN @(?)");

    function queryDatabase(constraints) {
      const result = compiledMasterQuery([constraints['peak-table2'],
                constraints['metabolite-table2'],
                constraints['pathway-table2'],
                constraints.identified,
                constraints.pValueCorrected,
                constraints.adjPValueCorrected,
                constraints.comparisonId]
              )
      return result;
    }

    function updateTables() {
      // if at top of stack don't redraw
      // focus table ignores its own constraints
      const dataForTables = {
        'peak-table2': [],
        'metabolite-table2': [],
        'pathway-table2': [],
      };

      const queryResult = queryDatabase(constraints);

      if (stack.stack.length > 0) {
        const focus = stack.stack[stack.stack.length - 1];
        const focusConstraints = {
          'peak-table2': (focus === 'peak-table2') ? defaultConstraints['peak-table2'] : constraints['peak-table2'],
          'metabolite-table2': (focus === 'metabolite-table2') ? defaultConstraints['metabolite-table2'] : constraints['metabolite-table2'],
          'pathway-table2': (focus === 'pathway-table2') ? defaultConstraints['pathway-table2'] : constraints['pathway-table2'],
          'identified': constraints['identified'],
          'pValueCorrected': constraints['pValueCorrected'],
          'adjPValueCorrected': constraints['adjPValueCorrected'],
          'comparisonId': constraints['comparisonId']
        };

        const focusResult = queryDatabase(focusConstraints);

        if (focus !== 'peak-table2') {
          dataForTables['peak-table2'] = alasql("SELECT DISTINCT peakPK, peakSecondaryId, mass, rt FROM ?", [queryResult]);
        } else {
          dataForTables['peak-table2'] = alasql("SELECT DISTINCT peakPK, peakSecondaryId, mass, rt FROM ?", [focusResult]);
        }
        peaksTableAPI.clear();
        peaksTableAPI.rows.add(dataForTables['peak-table2']);
        peaksTableAPI.draw();
        addSelectionStyle('peak-table2')

        if (focus !== 'metabolite-table2') {
          dataForTables['metabolite-table2'] = alasql("SELECT DISTINCT metaboliteSecondaryId, metaboliteName FROM ?", [queryResult]);
        } else {
          dataForTables['metabolite-table2'] = alasql("SELECT DISTINCT metaboliteSecondaryId, metaboliteName FROM ?", [focusResult]);
        }
        metabolitesTableAPI.clear();
        metabolitesTableAPI.rows.add(dataForTables['metabolite-table2']);
        metabolitesTableAPI.draw();
        addSelectionStyle('metabolite-table2')

        if (focus !== 'pathway-table2') {
          dataForTables['pathway-table2'] = alasql("SELECT DISTINCT pathwayPK, pathwayName FROM ?", [queryResult]);
        } else {
          dataForTables['pathway-table2'] = alasql("SELECT DISTINCT pathwayPK, pathwayName FROM ?", [focusResult]);
        }
        pathwaysTableAPI.clear();
        pathwaysTableAPI.rows.add(dataForTables['pathway-table2']);
        pathwaysTableAPI.draw();
        addSelectionStyle('pathway-table2');

      } else {
        resetTables();
      }
    }

    function resetTables() {
      // Clears and redraws the tables with their initial data
      const dataForTables = {
        'peak-table2': [],
        'metabolite-table2': [],
        'pathway-table2': [],
      };

      const queryResult = queryDatabase(constraints);

      dataForTables['peak-table2'] = alasql("SELECT DISTINCT peakPK, peakSecondaryId, mass, rt FROM ?", [queryResult]);
      dataForTables['metabolite-table2'] = alasql("SELECT DISTINCT metaboliteSecondaryId, metaboliteName FROM ?", [queryResult]);
      dataForTables['pathway-table2'] = alasql("SELECT DISTINCT pathwayPK, pathwayName FROM ?", [queryResult]);

      // Update the tables
      peaksTableAPI.clear();
      peaksTableAPI.rows.add(dataForTables['peak-table2']);
      peaksTableAPI.draw();

      metabolitesTableAPI.clear();
      metabolitesTableAPI.rows.add(dataForTables['metabolite-table2']);
      metabolitesTableAPI.draw();

      pathwaysTableAPI.clear();
      pathwaysTableAPI.rows.add(dataForTables['pathway-table2']);
      pathwaysTableAPI.draw();
    }

    function addSelectionStyle(tableId) {
      const tables = $('.dataTable').DataTable(),
            tableAPI = tables.table('#' + tableId),
            idNum = constraints[tableId];

      // idNum has a single element when a constraint (different from the initial constraint) is
      // applied.
      if (idNum.length === 1) {
        $(tableAPI.row('#' + idNum).node()).addClass('selected');

        // scroll to this row
        // TODO: call the scrolling code only when the row is out of the current datatables view

        // const tableScrollDOM = $('#' + tableId).parents('.dataTables_scrollBody');
        // const tableScrollDOMTop = tableScrollDOM.offset().top;
        // const tableScrollDOMBottom = tableScrollDOM.height() + tableScrollDOMTop;
        // const row = tableScrollDOM.find('#' + idNum);
        // const rowTop = row.offset().top;
        // const rowBottom = row.height() + rowTop;
        // const rowPosition = row.position();
        // console.log('row ', [rowTop, rowBottom], 'DOM', [tableScrollDOMTop, tableScrollDOMBottom]);
        // console.log('row position', row.position());
        //
        // if (rowPosition.top < 0) {
        //   tableScrollDOM.scrollTop(rowTop - tableScrollDOMTop + tableScrollDOM.scrollTop() - (tableScrollDOM.height()/2));
        //   console.log('riw is too hgith');
        // } else if ((rowPosition.top + row.height()) > tableScrollDOM.height()) {
        //   console.log('row is too low');
        //   tableScrollDOM.scrollTop(rowTop - tableScrollDOMTop + tableScrollDOM.scrollTop() - (tableScrollDOM.height()/2));
        // }

        const tableScrollDOM = $('#' + tableId).parents('.dataTables_scrollBody');
        const rowScrollPosition = tableScrollDOM.find('#' + idNum).offset();
        tableScrollDOM.scrollTop(tableScrollDOM.find('#' + idNum).offset().top - tableScrollDOM.offset().top + tableScrollDOM.scrollTop() - (tableScrollDOM.height()/2));
      }
    }

    function addConstraint(tableId, rowObject) {
      stack.addToStack(tableId);
      constraints[tableId] = [rowObject[tableIdToIdColumnMap[tableId]]];
      updateTables();
      getEntityInfo(tableId, rowObject);
    }

    function updateConstraint(tableId, rowObject) {
      stack.addToStack(tableId);
      constraints[tableId] = [rowObject[tableIdToIdColumnMap[tableId]]];
      updateTables();
      getEntityInfo(tableId, rowObject);
    }

    function removeConstraint(tableId) {
      stack.removeFromStack(tableId);
      constraints[tableId] = defaultConstraints[tableId];
      updateTables();
      clearInfoPane(tableId);
    }

    function clearInfoPane(tableId) {
      // Wrapper function to call the appropriate info function for the given table/entity
      if (tableId === 'peak-table2') {
        clearPeakInfo();
      } else if (tableId === 'metabolite-table2') {
        clearMetaboliteInfo();
      } else if (tableId === 'pathway-table2') {
        clearPathwayInfo();
      }
    }

    function getEntityInfo(tableId, rowObject) {
      // Wrapper function to call the appropriate info function for the given table/entity
      if (tableId === 'peak-table2') {
        getPeakInfo(rowObject)
      } else if (tableId === 'metabolite-table2') {
        getMetaboliteInfo(rowObject);
      } else if (tableId === 'pathway-table2') {
        getPathwayInfo(rowObject);
      }
    }

    const tableIdToIdColumnMap = {
      'peak-table2': 'peakPK',
      'metabolite-table2': 'metaboliteSecondaryId',
      'pathway-table2': 'pathwayPK'
    };

    function trClickHandler(e, dt, type, cell, originalEvent) {
      // Calls the appropriate constraint function depending on the state of the bound table
      // The column index of the relationship key is hardcoded in this function (it is 1)
      // selectedData is not used when removing a selection only

      e.preventDefault();
      const tableId = e.currentTarget.id,
            tables = $('.dataTable').DataTable(),
            tableAPI = tables.table('#' + tableId),
            selectedData = tableAPI.row('.selected').data(),
            targetTr = $(originalEvent.target).parent('tr'),
            rowObject = tableAPI.row(targetTr).data();

      // console.log("before", stack.stack, constraints);
      if ($('#' + tableId + ' tr').hasClass('selected')) {
        if (!targetTr.hasClass('selected')) {
          $('#' + tableId + ' .selected').removeClass('selected');
          updateConstraint(tableId, rowObject);
        } else {
          removeConstraint(tableId);
        }
      } else {
        addConstraint(tableId, rowObject);
      }
      // console.log("after", stack.stack, constraints);
    }

    // Initialise table clicks
    peaksTableAPI.on('user-select', trClickHandler);
    metabolitesTableAPI.on('user-select', trClickHandler);
    pathwaysTableAPI.on('user-select', trClickHandler);
  }); // end AJAX $.getJSON
}); // end $(document).ready
