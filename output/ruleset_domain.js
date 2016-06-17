function setup_ui(){
  var domain = document.location.pathname.replace(/\/domains\//, '').replace(/(-[0-9]+)?.html/,'');
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
    document.getElementById("stable_affected").style.display = "none";
  }
  if(!release_affected){
    document.getElementById("release_affected").style.display = "none";
  }
}
