function setup_ui(){
  var domain = document.location.pathname.replace(/^.*\/domains\//, '').replace(/(-[0-9]+)?.html/,'');
  var stable_affected = (stable_hosts.indexOf(domain) != -1);
  var release_affected = (release_hosts.indexOf(domain) != -1);

  document.getElementById("domain_name").innerHTML = domain;

  var affected_releases = "";
  if(stable_affected && release_affected){
    affected_releases = "<a href='https://www.eff.org/https-everywhere'>HTTPS Everywhere</a> currently rewrites requests to <b>" + domain + "</b> (or its subdomains)."
  } else if(stable_affected){
    affected_releases = "The master branch of <a href='https://www.eff.org/https-everywhere'>HTTPS Everywhere</a> currently rewrites requests to <b>" + domain + "</b> (or its subdomains). These rewrites will take effect in a future release.";
  } else if(release_affected){
    affected_releases = "<a href='https://www.eff.org/https-everywhere'>HTTPS Everywhere</a> currently rewrites requests to <b>" + domain + "</b> (or its subdomains).";
  }
  document.getElementById("affected_releases").innerHTML = affected_releases;

  if(!stable_affected){
    var stable_affected_div = document.getElementById("stable_affected");
    if(stable_affected_div){
      stable_affected_div.style.display = "none";
    }
  }
  if(!release_affected){
    var release_affected_div = document.getElementById("release_affected");
    if(release_affected_div){
      release_affected_div.style.display = "none";
    }

  }
}
